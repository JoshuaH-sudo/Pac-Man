"""Arcade game view, maze rendering, and gameplay setup."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

import arcade
import arcade.gui

from mazegenerator import MazeGenerator

from pacman.core import (
    GHOST_CELL_FRACTION,
    GHOST_SPEED_RATIO,
    ITEM_CELL_FRACTION,
    PLAYER_CELL_FRACTION,
    PLAYER_MOVEMENT_SPEED,
    PLAYER_SPEED_RATIO,
    WINDOW_WIDTH,
    center_cell_index,
    choose_initial_direction,
    direction_is_open,
    nearest_cell_index,
)
from pacman.entities import Ghost, Pacgum, Pacman, SuperPacgum
from pacman.game.state import GameState
from pacman.maze import (
    MazeDisplay,
    build_corner_cells,
    build_item_cells,
    build_super_item_cells,
)
from pacman.input import MovementController

if TYPE_CHECKING:
    from pacman.core import GameConfig
    from pacman.ui.main_menu import MainMenu

LOGGER = logging.getLogger(__name__)
GHOST_VULNERABILITY_DURATION_SECONDS = 6.0
GHOST_SPRITE_SHEETS: tuple[str, ...] = (
    "Blinky.png",
    "Pinky.png",
    "Inky.png",
    "Clyde.png",
)


# Backward-compatible aliases for existing tests and imports.
_build_item_cells = build_item_cells
_build_corner_cells = build_corner_cells
_build_super_item_cells = build_super_item_cells


def _env_flag_is_enabled(name: str) -> bool:
    """Return True when the environment flag is set to a truthy value."""
    return os.getenv(name, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "debug",
    }


class GameView(arcade.View):
    """Main game view that renders maze, entities, and update loop."""

    def __init__(self, config: GameConfig, state: GameState,
                 main_menu: "MainMenu | None" = None) -> None:
        super().__init__()

        self.config = config
        self.state = state
        self.main_menu = main_menu

        self.cheat_mode = False

        # Initialize entity sprite lists (empty, will be populated by _load_level)
        self._player = Pacman(
            center_x=0.0,
            center_y=0.0,
            speed=PLAYER_MOVEMENT_SPEED,
            scale=1.0,
        )
        self._players: arcade.SpriteList[Pacman] = arcade.SpriteList()
        self._players.append(self._player)
        self._walls: arcade.SpriteList[arcade.SpriteSolidColor] = (
            arcade.SpriteList(use_spatial_hash=True)
        )
        self._physics_engine: arcade.PhysicsEngineSimple | None = None

        self._items: arcade.SpriteList[arcade.Sprite] = arcade.SpriteList()
        self._ghosts: arcade.SpriteList[Ghost] = arcade.SpriteList()
        for ghost_sheet in GHOST_SPRITE_SHEETS:
            self._ghosts.append(
                Ghost(
                    sprite_sheet_name=ghost_sheet,
                    center_x=0.0,
                    center_y=0.0,
                    speed=PLAYER_MOVEMENT_SPEED,
                    scale=1.0,
                )
            )

        # Maze grid will be set by _load_level
        self._maze_grid: tuple[tuple[int, ...], ...] = ()
        self._maze_display: MazeDisplay | None = None
        self._player_cell_x = 0
        self._player_cell_y = 0
        self._item_cells: tuple[tuple[float, float], ...] = ()
        self._super_item_cells: tuple[tuple[float, float], ...] = ()
        self._all_item_cells: tuple[tuple[float, float], ...] = ()
        self._count_pacgums = 0
        self._ghost_cells: tuple[tuple[float, float], ...] = ()
        self._initialized = False
        self._level_loaded = False

        # Movement controller will be initialized in _load_level
        self._movement = MovementController((0, 0))

        self.manager = arcade.gui.UIManager()
        self.anchor = self.manager.add(arcade.gui.UIAnchorLayout())
        pause_button = arcade.gui.UIFlatButton(text="Pause", width=80, height=30)
        self.anchor.add(
            anchor_x="right",
            anchor_y="top",
            align_x=-10,
            align_y=-10,
            child=pause_button,
        )

        @pause_button.event("on_click")
        def on_click_pause_button(event: arcade.gui.UIOnClickEvent) -> None:
            self._open_pause_menu()

        # HUD
        self._level_label = arcade.gui.UILabel(text="Level: 1", font_size=14)
        self._lives_label = arcade.gui.UILabel(text="Lives: 0", font_size=14)
        self._score_label = arcade.gui.UILabel(text="Score: 0", font_size=14)
        self._timer_label = arcade.gui.UILabel(text="Timer: 0", font_size=14)

        self.hud_box = arcade.gui.UIBoxLayout(vertical=True, space_between=4,
                                              align="left")
        self.hud_box.add(self._level_label)
        self.hud_box.add(self._lives_label)
        self.hud_box.add(self._score_label)
        self.hud_box.add(self._timer_label)

        self.anchor.add(
            anchor_x="left",
            anchor_y="bottom",
            align_x=12,
            align_y=12,
            child=self.hud_box,
        )

        self.cheat_mode_text = arcade.Text("Cheat mode", WINDOW_WIDTH - 125, 12,
                                           font_size=14, align="center")

        self._ghost_vulnerability_remaining = 0.0
        self._debug_enabled = _env_flag_is_enabled("PACMAN_DEBUG")
        if self._debug_enabled:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            )
            LOGGER.debug("PACMAN_DEBUG enabled for movement tracing")

    def _load_level(self) -> None:
        """Generate and initialize a new maze for the current level."""
        # Get level dimensions from config
        level_width, level_height = self.config.levels[self.state.level - 1]

        # Generate a new maze
        generator = MazeGenerator(
            size=(level_width, level_height),
            perfect=False,
            seed=self.config.seed if self.state.level == 1 else 0,
        )
        maze_grid = generator.maze

        msg = (f"Level {self.state.level}: Maze dimensions: "
               f"{len(maze_grid[0])}x{len(maze_grid)}")
        print(msg)
        for row in maze_grid:
            # print hexadecimal values for better visualization
            print("".join(f"{cell:2X}" for cell in row))

        # Convert maze grid to tuple of tuples
        self._maze_grid = tuple(
            tuple(int(cell) for cell in row) for row in maze_grid
        )

        # Create maze display
        self._maze_display = MazeDisplay(maze_grid)

        # Calculate player starting position
        self._player_cell_x = center_cell_index(self._maze_display.cols)
        self._player_cell_y = center_cell_index(self._maze_display.rows)

        # Build item cells for this level
        self._item_cells = _build_item_cells(self._maze_grid)
        self._super_item_cells = _build_super_item_cells(self._maze_grid)
        self._all_item_cells = self._item_cells + self._super_item_cells
        self._count_pacgums = len(self._all_item_cells)

        # Build ghost spawn cells
        self._ghost_cells = _build_corner_cells(
            self._maze_display.cols,
            self._maze_display.rows,
        )

        # Clear old items
        self._items.clear()

        # Create new items for this level
        for _ in self._item_cells:
            self._items.append(
                Pacgum(
                    center_x=0.0,
                    center_y=0.0,
                    scale=1.0,
                )
            )
        for _ in self._super_item_cells:
            self._items.append(
                SuperPacgum(
                    center_x=0.0,
                    center_y=0.0,
                    scale=1.0,
                )
            )

        # Initialize movement controller
        center_cell_value = int(
            maze_grid[self._player_cell_y][self._player_cell_x]
        )
        self._movement = MovementController(
            choose_initial_direction(center_cell_value)
        )

        # Reset ghost vulnerability when level starts
        self._ghost_vulnerability_remaining = 0.0
        self._set_all_ghosts_vulnerable(False)

        self._level_loaded = True

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        if not self._level_loaded:
            self._load_level()
        if not self._initialized:
            self._sync_entities_to_maze()
            self._initialized = True
        self.manager.enable()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self._sync_entities_to_maze()
        self.manager.disable()

    def on_draw(self) -> None:
        self.clear()
        if self._maze_display is not None:
            self._maze_display.draw(self.window.width, self.window.height)
        self._items.draw()
        self._players.draw()
        self._ghosts.draw()
        self._update_label_text(self._timer_label, f"Timer: {int(self.state.timer)}")
        self._update_label_text(self._score_label, f"Score: {self.state.score}")
        self._update_label_text(self._lives_label, f"Lives: {self.state.lives}")
        self._update_label_text(self._level_label, f"Level: {self.state.level}")
        self.manager.draw()
        if self.cheat_mode:
            self.cheat_mode_text.draw()

    def on_update(self, delta_time: float) -> None:
        if self.window is None or self._maze_display is None:
            return

        self._update_ghost_vulnerability(delta_time)

        prev_x = self._player.center_x
        prev_y = self._player.center_y
        cell_x, cell_y = self._current_cell_indices()
        cell_value = int(self._maze_grid[cell_y][cell_x])

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        direction, center_x, center_y, _ = self._movement.apply(
            self._player.center_x,
            self._player.center_y,
            cell_size,
            offset_x,
            offset_y,
            cell_value,
        )
        self._player.center_x = center_x
        self._player.center_y = center_y
        self._player.move(horizontal=direction[0], vertical=direction[1])

        if self._physics_engine is None:
            self._players.update()
        else:
            self._physics_engine.update()

        self._update_ghosts()
        self._ghosts.update()

        self._player.snap_to_lane(
            direction=direction,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
            max_alignment_step=max(
                abs(self._player.change_x), abs(self._player.change_y)
            ),
        )
        if self._debug_enabled:
            current_direction, desired_direction, queued_direction, spawn_lock = (
                self._movement.debug_state()
            )
            LOGGER.debug(
                "player_update cell=(%d,%d) pos=(%.2f,%.2f)->(%.2f,%.2f) "
                "delta=(%.2f,%.2f) speed=(%.2f,%.2f) current=%s desired=%s queued=%s "
                "spawn_lock=%s open={up:%s,right:%s,down:%s,left:%s}",
                cell_x,
                cell_y,
                prev_x,
                prev_y,
                self._player.center_x,
                self._player.center_y,
                self._player.center_x - prev_x,
                self._player.center_y - prev_y,
                self._player.change_x,
                self._player.change_y,
                current_direction,
                desired_direction,
                queued_direction,
                spawn_lock,
                direction_is_open(cell_value, (0, 1)),
                direction_is_open(cell_value, (1, 0)),
                direction_is_open(cell_value, (0, -1)),
                direction_is_open(cell_value, (-1, 0)),
            )
        self._collect_item_collisions()
        self._players.update_animation(delta_time=delta_time)
        self._items.update_animation(delta_time=delta_time)
        self._keep_player_on_screen()

        self.state.timer -= delta_time

        all_gums_eaten = (
            self.state.pacgums_eaten + self.state.super_pacgums_eaten
        )

        # Check if level is completed
        if self.state.lives > 0 and self.state.timer >= 0 \
                and all_gums_eaten >= self._count_pacgums:
            # Level completed
            self.state.advance_level()

            # If we haven't reached the maximum levels, load the new level
            if self.state.level <= len(self.config.levels):
                self._load_level()
                self._sync_entities_to_maze()

        # End game conditions
        if self.state.lives <= 0 or (self.state.timer < 0
                                     and all_gums_eaten < self._count_pacgums):
            self._show_endscreen(False)
        elif self.state.lives > 0 and self.state.level > len(
                self.config.levels):
            self._show_endscreen(True)

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        cell_value: int | None = None
        if self.window is not None:
            cell_value = self._current_cell_value()
        self._movement.queue_input(symbol, cell_value)

        if symbol == arcade.key.P and self.main_menu is not None:
            self._open_pause_menu()

        if not self.cheat_mode:
            if symbol == arcade.key.C:
                self.cheat_mode = True
        else:
            if symbol == arcade.key.C:
                self.cheat_mode = False

            # Shortcut to pause and end screens
            if symbol == arcade.key.O:
                self._show_endscreen(False)

            if symbol == arcade.key.V:
                self._show_endscreen(True)

            # Shortcut to next level
            if symbol == arcade.key.N:
                self.state.advance_level()

                # If we haven't reached the maximum levels, load the new level
                if self.state.level <= len(self.config.levels):
                    self._load_level()
                    self._sync_entities_to_maze()

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        del modifiers
        del symbol

    def _keep_player_on_screen(self) -> None:
        width = self.window.width
        height = self.window.height
        half_w = self._player.width / 2
        half_h = self._player.height / 2

        self._player.center_x = max(
            half_w,
            min(width - half_w, self._player.center_x),
        )
        self._player.center_y = max(
            half_h,
            min(height - half_h, self._player.center_y),
        )

    def _sync_entities_to_maze(self) -> None:
        if self.window is None or self._maze_display is None:
            return

        self._player_cell_x = max(
            0,
            min(self._maze_display.cols - 1, int(round(self._player_cell_x))),
        )
        self._player_cell_y = max(
            0,
            min(self._maze_display.rows - 1, int(round(self._player_cell_y))),
        )

        cell_size, _, _ = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )

        self._player.scale = (cell_size * PLAYER_CELL_FRACTION) / max(
            1.0, float(self._player.texture.width)
        )
        self._player.set_speed(cell_size * PLAYER_SPEED_RATIO)
        self._player.center_x, self._player.center_y = self._maze_display.cell_center(
            self.window.width,
            self.window.height,
            float(self._player_cell_x),
            float(self._player_cell_y),
        )
        self._rebuild_wall_colliders()
        center_cell_value = int(
            self._maze_grid[self._player_cell_y][self._player_cell_x]
        )
        self._movement.reset(choose_initial_direction(center_cell_value))

        for item, (cell_x, cell_y) in zip(self._items, self._all_item_cells):
            item.scale = (cell_size * ITEM_CELL_FRACTION) / max(
                1.0, float(item.texture.width)
            )
            item.center_x, item.center_y = self._maze_display.cell_center(
                self.window.width,
                self.window.height,
                cell_x,
                cell_y,
            )

        for index, (ghost, (cell_x, cell_y)) in enumerate(
            zip(self._ghosts, self._ghost_cells)
        ):
            ghost.scale = (cell_size * GHOST_CELL_FRACTION) / max(
                1.0, float(ghost.texture.width)
            )
            ghost.set_speed(cell_size * GHOST_SPEED_RATIO)
            ghost.center_x, ghost.center_y = self._maze_display.cell_center(
                self.window.width,
                self.window.height,
                cell_x,
                cell_y,
            )
            cell_value = int(self._maze_grid[int(cell_y)][int(cell_x)])
            ghost.set_spawn_direction(cell_value)

    def _update_ghosts(self) -> None:
        """Delegate maze-aware movement updates to ghost entities."""
        if self.window is None or self._maze_display is None:
            return

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        player_cell_x, player_cell_y = self._current_cell_indices()
        player_direction = self._movement.current_direction

        ghost_cells = [
            self._cell_indices_for_position(ghost.center_x, ghost.center_y)
            for ghost in self._ghosts
        ]
        blinky_cell = (
            ghost_cells[0] if ghost_cells else (player_cell_x, player_cell_y)
        )

        for index, (ghost, (cell_x, cell_y)) in enumerate(
            zip(self._ghosts, ghost_cells)
        ):
            cell_value = int(self._maze_grid[cell_y][cell_x])
            target_cell_x, target_cell_y = self._target_tile_for_ghost(
                ghost_index=index,
                ghost_cell_x=cell_x,
                ghost_cell_y=cell_y,
                player_cell_x=player_cell_x,
                player_cell_y=player_cell_y,
                player_direction=player_direction,
                blinky_cell_x=blinky_cell[0],
                blinky_cell_y=blinky_cell[1],
            )

            center_x, center_y = self._maze_display.cell_center(
                self.window.width,
                self.window.height,
                float(cell_x),
                float(cell_y),
            )
            ghost.update_maze_movement(
                cell_value=cell_value,
                center_x=center_x,
                center_y=center_y,
                cell_size=cell_size,
                offset_x=offset_x,
                offset_y=offset_y,
                maze_grid=self._maze_grid,
                ghost_cell_x=cell_x,
                ghost_cell_y=cell_y,
                target_cell_x=target_cell_x,
                target_cell_y=target_cell_y,
            )

    def _target_tile_for_ghost(
        self,
        ghost_index: int,
        ghost_cell_x: int,
        ghost_cell_y: int,
        player_cell_x: int,
        player_cell_y: int,
        player_direction: tuple[int, int],
        blinky_cell_x: int,
        blinky_cell_y: int,
    ) -> tuple[int, int]:
        """Return target tile for ghost personality (Blinky/Pinky/Inky/Clyde)."""
        # Vulnerable mode uses flee logic in Ghost; pass player tile so ghosts
        # run away from Pac-Man consistently regardless of personality.
        if self._ghost_vulnerability_remaining > 0.0:
            return player_cell_x, player_cell_y

        if ghost_index == 0:
            # Blinky: direct chaser.
            return player_cell_x, player_cell_y

        if ghost_index == 1:
            # Pinky: target 4 tiles ahead of Pac-Man heading.
            return self._tile_ahead_of_player(
                player_cell_x,
                player_cell_y,
                player_direction,
                steps=4,
            )

        if ghost_index == 2:
            # Inky: build vector from Blinky to 2-ahead tile, then double it.
            ahead_x, ahead_y = self._tile_ahead_of_player(
                player_cell_x,
                player_cell_y,
                player_direction,
                steps=2,
            )
            vector_x = ahead_x - blinky_cell_x
            vector_y = ahead_y - blinky_cell_y
            return self._clamp_cell_indices(
                ahead_x + vector_x,
                ahead_y + vector_y,
            )

        # Clyde: chase when far, switch to bottom-left corner when within 8.
        if self._manhattan_distance(
            ghost_cell_x,
            ghost_cell_y,
            player_cell_x,
            player_cell_y,
        ) <= 8:
            if self._maze_display is not None:
                return self._clamp_cell_indices(0, self._maze_display.rows - 1)
        return player_cell_x, player_cell_y

    def _tile_ahead_of_player(
        self,
        player_cell_x: int,
        player_cell_y: int,
        player_direction: tuple[int, int],
        steps: int,
    ) -> tuple[int, int]:
        """Return clamped tile N steps ahead of player heading.

        Grid row indices increase downward, so world-space +Y maps to row -1.
        """
        target_x = player_cell_x + (player_direction[0] * steps)
        target_y = player_cell_y - (player_direction[1] * steps)
        return self._clamp_cell_indices(target_x, target_y)

    def _clamp_cell_indices(self, cell_x: int, cell_y: int) -> tuple[int, int]:
        """Clamp raw cell coordinates into current maze bounds."""
        if self._maze_display is None:
            return cell_x, cell_y
        clamped_x = max(0, min(self._maze_display.cols - 1, cell_x))
        clamped_y = max(0, min(self._maze_display.rows - 1, cell_y))
        return clamped_x, clamped_y

    @staticmethod
    def _manhattan_distance(
        cell_x1: int,
        cell_y1: int,
        cell_x2: int,
        cell_y2: int,
    ) -> int:
        """Return Manhattan distance between two grid cells."""
        return abs(cell_x1 - cell_x2) + abs(cell_y1 - cell_y2)

    def _collect_item_collisions(self) -> None:
        """Consume collided pacgums and apply score updates."""
        collided_items = arcade.check_for_collision_with_list(self._player, self._items)
        for item in collided_items:
            item.remove_from_sprite_lists()
            if isinstance(item, SuperPacgum):
                self._ghost_vulnerability_remaining = (
                    GHOST_VULNERABILITY_DURATION_SECONDS
                )
                self._set_all_ghosts_vulnerable(True)
                self.state.add_super_pacgum(
                    self.config.points_per_super_pacgum
                    if self.config is not None
                    else SuperPacgum.POINT_VALUE
                )
            elif isinstance(item, Pacgum):
                self.state.add_pacgum(
                    self.config.points_per_pacgum
                    if self.config is not None
                    else Pacgum.POINT_VALUE
                )

    def _update_ghost_vulnerability(self, delta_time: float) -> None:
        """Expire ghost vulnerability state when the super-pacgum window ends."""
        if self._ghost_vulnerability_remaining <= 0.0:
            return

        self._ghost_vulnerability_remaining = max(
            0.0, self._ghost_vulnerability_remaining - delta_time
        )
        if self._ghost_vulnerability_remaining == 0.0:
            self._set_all_ghosts_vulnerable(False)

    def _set_all_ghosts_vulnerable(self, is_vulnerable: bool) -> None:
        """Apply vulnerability visuals to all ghosts at once."""
        for ghost in self._ghosts:
            ghost.set_vulnerable(is_vulnerable)

    def _current_cell_value(self) -> int:
        """Return wall flags for the maze cell currently containing the player."""
        cell_x, cell_y = self._current_cell_indices()
        return int(self._maze_grid[cell_y][cell_x])

    def _current_cell_indices(self) -> tuple[int, int]:
        """Return the nearest maze cell indices for the current player position."""
        return self._cell_indices_for_position(
            self._player.center_x,
            self._player.center_y,
        )

    def _cell_indices_for_position(
        self,
        center_x: float,
        center_y: float,
    ) -> tuple[int, int]:
        """Return nearest maze cell indices for a world-space position."""
        if self.window is None or self._maze_display is None:
            return self._player_cell_x, self._player_cell_y

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        cell_x = nearest_cell_index(center_x, offset_x, cell_size)
        cell_y = nearest_cell_index(
            self.window.height - center_y,
            offset_y,
            cell_size,
        )
        cell_x = max(0, min(self._maze_display.cols - 1, cell_x))
        cell_y = max(0, min(self._maze_display.rows - 1, cell_y))
        return cell_x, cell_y

    def _rebuild_wall_colliders(self) -> None:
        """Recreate collision sprites so walls match the current maze layout."""
        if self.window is None or self._maze_display is None:
            return

        walls: arcade.SpriteList[arcade.SpriteSolidColor] = (
            arcade.SpriteList(use_spatial_hash=True)
        )
        for center_x, center_y, width, height in self._maze_display.wall_colliders(
            self.window.width,
            self.window.height,
        ):
            wall = arcade.SpriteSolidColor(
                max(1, round(width)),
                max(1, round(height)),
                color=(0, 0, 0, 0),
            )
            wall.center_x = center_x
            wall.center_y = center_y
            walls.append(wall)

        self._walls = walls
        self._physics_engine = arcade.PhysicsEngineSimple(self._player, self._walls)

    def _open_pause_menu(self) -> None:
        if self.window is None or self.main_menu is None:
            return

        from pacman.ui.pause_menu import PauseMenu

        self.window.show_view(PauseMenu(self.config, game=self))

    @staticmethod
    def _update_label_text(label: arcade.gui.UILabel, text: str) -> None:
        """Only assign new text when it changed, to avoid unnecessary relayout."""
        if label.text != text:
            label.text = text

    def _show_endscreen(self, won: bool) -> None:
        if self.window is None:
            return

        from pacman.ui.end_screen import EndScreen

        if won:
            message = "You won!"
            color = arcade.color.YELLOW
        else:
            message = "Game over!"
            color = arcade.color.WHITE

        self.window.show_view(
            EndScreen(
                message=message,
                color=color,
                score=self.state.score,
                config=self.config,
                game=self,
            )
        )
