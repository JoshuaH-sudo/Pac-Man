"""Arcade game view, maze rendering, and gameplay setup."""

from __future__ import annotations

import logging
import os
from typing import Sequence

import arcade

from pacman.core import (
    GHOST_CELL_FRACTION,
    GHOST_SPEED_RATIO,
    ITEM_CELL_FRACTION,
    PACGUM_ANIMATION_FPS,
    PLAYER_CELL_FRACTION,
    PLAYER_MOVEMENT_SPEED,
    PLAYER_SPEED_RATIO,
    center_cell_index,
    choose_initial_direction,
    direction_is_open,
    nearest_cell_index,
)
from pacman.entities import Ghost, Pacgum, Pacman
from pacman.maze import MazeDisplay, build_corner_cells, build_item_cells
from pacman.input import MovementController

LOGGER = logging.getLogger(__name__)
GHOST_SPRITE_SHEETS: tuple[str, ...] = (
    "Blinky.png",
    "Pinky.png",
    "Inky.png",
    "Clyde.png",
)


# Backward-compatible aliases for existing tests and imports.
_build_item_cells = build_item_cells
_build_corner_cells = build_corner_cells


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

    def __init__(self, maze_grid: Sequence[Sequence[int]]):
        super().__init__()
        self._maze_grid = tuple(tuple(int(cell) for cell in row) for row in maze_grid)
        self._maze_display = MazeDisplay(maze_grid)
        self._player_cell_x = center_cell_index(self._maze_display.cols)
        self._player_cell_y = center_cell_index(self._maze_display.rows)
        self._item_cells = _build_item_cells(self._maze_grid)
        self._ghost_cells = _build_corner_cells(
            self._maze_display.cols,
            self._maze_display.rows,
        )

        center_cell_value = int(maze_grid[self._player_cell_y][self._player_cell_x])

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

        self._items: arcade.SpriteList[Pacgum] = arcade.SpriteList()
        for _ in self._item_cells:
            self._items.append(
                Pacgum(
                    center_x=0.0,
                    center_y=0.0,
                    scale=1.0,
                    animation_fps=PACGUM_ANIMATION_FPS,
                )
            )

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

        self._movement = MovementController(choose_initial_direction(center_cell_value))
        self._debug_enabled = _env_flag_is_enabled("PACMAN_DEBUG")
        if self._debug_enabled:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            )
            LOGGER.debug("PACMAN_DEBUG enabled for movement tracing")

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self._sync_entities_to_maze()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self._sync_entities_to_maze()

    def on_draw(self) -> None:
        self.clear()
        self._maze_display.draw(self.window.width, self.window.height)
        self._items.draw()
        self._players.draw()
        self._ghosts.draw()

    def on_update(self, delta_time: float) -> None:
        if self.window is None:
            return

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

        self._player.center_x, self._player.center_y = self._movement.snap_to_lane(
            self._player.center_x,
            self._player.center_y,
            cell_size,
            offset_x,
            offset_y,
            max(abs(self._player.change_x), abs(self._player.change_y)),
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
        self._players.update_animation(delta_time=delta_time)
        self._items.update_animation(delta_time=delta_time)
        self._keep_player_on_screen()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        cell_value: int | None = None
        if self.window is not None:
            cell_value = self._current_cell_value()
        self._movement.queue_input(symbol, cell_value)

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
        if self.window is None:
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

        for item, (cell_x, cell_y) in zip(self._items, self._item_cells):
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
        if self.window is None:
            return

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        for ghost in self._ghosts:
            cell_x, cell_y = self._cell_indices_for_position(
                ghost.center_x,
                ghost.center_y,
            )
            cell_value = int(self._maze_grid[cell_y][cell_x])

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
            )

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
        if self.window is None:
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
        if self.window is None:
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
