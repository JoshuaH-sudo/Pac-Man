"""Arcade game view, maze rendering, and gameplay setup."""

from __future__ import annotations

from dataclasses import dataclass
import logging
import os
from typing import Sequence

import arcade
from arcade.types import Color

from pacman.constants import (
    CLOSED_EAST,
    CLOSED_NORTH,
    CLOSED_SOUTH,
    CLOSED_WEST,
    COLLISION_WALL_THICKNESS_RATIO,
    ITEM_CELL_FRACTION,
    MAZE_MARGIN,
    MAX_COLLISION_WALL_THICKNESS,
    PACGUM_ANIMATION_FPS,
    PLAYER_CELL_FRACTION,
    PLAYER_MOVEMENT_SPEED,
    PLAYER_SPEED_RATIO,
)
from pacman.entities import Pacgum, Pacman
from pacman.movement import MovementController
from pacman.types import GridPoint, WallCollider, WallSegment
from pacman.utils import (
    center_cell_index,
    choose_initial_direction,
    direction_is_open,
    nearest_cell_index,
    normalize_segment,
)

LOGGER = logging.getLogger(__name__)


def _env_flag_is_enabled(name: str) -> bool:
    """Return True when the environment flag is set to a truthy value."""
    return os.getenv(name, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "debug",
    }


@dataclass(frozen=True)
class MazePointGrid:
    """Point-grid representation derived from integer maze cells."""

    rows: int
    cols: int
    points: tuple[GridPoint, ...]
    wall_segments: tuple[WallSegment, ...]

    @classmethod
    def from_maze_grid(
        cls,
        maze_grid: Sequence[Sequence[int]],
    ) -> "MazePointGrid":
        """Parse maze cell bitmasks into corner points and wall segments."""
        if not maze_grid or not maze_grid[0]:
            raise ValueError(
                "maze_grid must be a non-empty rectangular matrix"
            )

        rows = len(maze_grid)
        cols = len(maze_grid[0])
        if any(len(row) != cols for row in maze_grid):
            raise ValueError("maze_grid rows must have equal length")

        points = tuple(
            (x, y)
            for y in range(rows + 1)
            for x in range(cols + 1)
        )
        wall_segments: set[WallSegment] = set()

        for y, row in enumerate(maze_grid):
            for x, cell in enumerate(row):
                cell_value = int(cell)
                if cell_value & CLOSED_NORTH:
                    wall_segments.add(normalize_segment((x, y), (x + 1, y)))
                if cell_value & CLOSED_EAST:
                    wall_segments.add(
                        normalize_segment((x + 1, y), (x + 1, y + 1))
                    )
                if cell_value & CLOSED_SOUTH:
                    wall_segments.add(
                        normalize_segment((x, y + 1), (x + 1, y + 1))
                    )
                if cell_value & CLOSED_WEST:
                    wall_segments.add(normalize_segment((x, y), (x, y + 1)))

        return cls(
            rows=rows,
            cols=cols,
            points=points,
            wall_segments=tuple(sorted(wall_segments)),
        )


class MazeDisplay:
    """Render maze walls from a point-grid onto an Arcade view."""

    def __init__(
        self,
        maze_grid: Sequence[Sequence[int]],
        margin: float = MAZE_MARGIN,
        wall_color: Color = arcade.color.ALICE_BLUE,
        wall_width: float = 2.0,
    ) -> None:
        self._point_grid = MazePointGrid.from_maze_grid(maze_grid)
        self._margin = margin
        self._wall_color = wall_color
        self._wall_width = wall_width

    def draw(self, window_width: int, window_height: int) -> None:
        """Draw all closed walls scaled to the current window size."""
        cell_size, offset_x, offset_y = self.layout_for_window(
            window_width,
            window_height,
        )

        for (
            (start_x, start_y),
            (end_x, end_y),
        ) in self._point_grid.wall_segments:
            x1 = offset_x + start_x * cell_size
            y1 = window_height - (offset_y + start_y * cell_size)
            x2 = offset_x + end_x * cell_size
            y2 = window_height - (offset_y + end_y * cell_size)
            arcade.draw_line(
                x1,
                y1,
                x2,
                y2,
                self._wall_color,
                self._wall_width,
            )

    def wall_colliders(
        self,
        window_width: int,
        window_height: int,
    ) -> tuple[WallCollider, ...]:
        """Return wall-aligned collision boxes for the current window size."""
        cell_size, offset_x, offset_y = self.layout_for_window(
            window_width,
            window_height,
        )
        thickness = max(
            1.0,
            min(
                max(self._wall_width * 2.0, 1.0),
                cell_size * COLLISION_WALL_THICKNESS_RATIO,
                MAX_COLLISION_WALL_THICKNESS,
            ),
        )
        colliders: list[WallCollider] = []

        for (start_x, start_y), (end_x, end_y) in self._point_grid.wall_segments:
            if start_x == end_x:
                colliders.append(
                    (
                        offset_x + start_x * cell_size,
                        window_height
                        - (offset_y + ((start_y + end_y) * cell_size / 2.0)),
                        thickness,
                        abs(end_y - start_y) * cell_size + thickness,
                    )
                )
                continue

            colliders.append(
                (
                    offset_x + ((start_x + end_x) * cell_size / 2.0),
                    window_height - (offset_y + start_y * cell_size),
                    abs(end_x - start_x) * cell_size + thickness,
                    thickness,
                )
            )

        return tuple(colliders)

    @property
    def rows(self) -> int:
        """Maze row count in cells."""
        return self._point_grid.rows

    @property
    def cols(self) -> int:
        """Maze column count in cells."""
        return self._point_grid.cols

    def layout_for_window(
        self,
        window_width: int,
        window_height: int,
    ) -> tuple[float, float, float]:
        """Compute scale and offsets that center the maze in the viewport."""
        usable_w = max(1.0, window_width - (self._margin * 2.0))
        usable_h = max(1.0, window_height - (self._margin * 2.0))

        cell_size = min(
            usable_w / self._point_grid.cols,
            usable_h / self._point_grid.rows,
        )
        offset_x = (window_width - self._point_grid.cols * cell_size) / 2.0
        offset_y = (window_height - self._point_grid.rows * cell_size) / 2.0
        return cell_size, offset_x, offset_y

    def cell_center(
        self,
        window_width: int,
        window_height: int,
        cell_x: float,
        cell_y: float,
    ) -> tuple[float, float]:
        """Return on-screen center coordinates for a maze cell coordinate."""
        cell_size, offset_x, offset_y = self.layout_for_window(
            window_width,
            window_height,
        )
        center_x = offset_x + (cell_x + 0.5) * cell_size
        center_y = window_height - (offset_y + (cell_y + 0.5) * cell_size)
        return center_x, center_y


class GameView(arcade.View):
    """Main game view that renders maze, entities, and update loop."""

    def __init__(self, maze_grid: Sequence[Sequence[int]]):
        super().__init__()
        self._maze_grid = tuple(tuple(int(cell) for cell in row) for row in maze_grid)
        self._maze_display = MazeDisplay(maze_grid)
        self._player_cell_x = center_cell_index(self._maze_display.cols)
        self._player_cell_y = center_cell_index(self._maze_display.rows)
        self._item_cell_x = min(
            self._maze_display.cols - 1,
            self._player_cell_x + 2,
        )
        self._item_cell_y = max(0, self._player_cell_y - 2)

        center_cell_value = int(
            maze_grid[self._player_cell_y][self._player_cell_x]
        )

        self._player = Pacman(
            center_x=0.0,
            center_y=0.0,
            speed=PLAYER_MOVEMENT_SPEED,
            scale=1.0,
        )
        self._players: arcade.SpriteList = arcade.SpriteList()
        self._players.append(self._player)
        self._walls: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        self._physics_engine: arcade.PhysicsEngineSimple | None = None

        self._items: arcade.SpriteList = arcade.SpriteList()
        self._items.append(
            Pacgum(
                center_x=0.0,
                center_y=0.0,
                scale=1.0,
                animation_fps=PACGUM_ANIMATION_FPS,
            )
        )

        self._movement = MovementController(
            choose_initial_direction(center_cell_value)
        )
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

        self._player.center_x, self._player.center_y = self._movement.snap_to_lane(
            self._player.center_x,
            self._player.center_y,
            cell_size,
            offset_x,
            offset_y,
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

        self._player.scale = (
            (cell_size * PLAYER_CELL_FRACTION)
            / max(1.0, float(self._player.texture.width))
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

        for item in self._items:
            item.scale = (
                (cell_size * ITEM_CELL_FRACTION)
                / max(1.0, float(item.texture.width))
            )
            item.center_x, item.center_y = self._maze_display.cell_center(
                self.window.width,
                self.window.height,
                self._item_cell_x,
                self._item_cell_y,
            )

    def _current_cell_value(self) -> int:
        """Return wall flags for the maze cell currently containing the player."""
        cell_x, cell_y = self._current_cell_indices()
        return int(self._maze_grid[cell_y][cell_x])

    def _current_cell_indices(self) -> tuple[int, int]:
        """Return the nearest maze cell indices for the current player position."""
        if self.window is None:
            return self._player_cell_x, self._player_cell_y

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        cell_x = nearest_cell_index(self._player.center_x, offset_x, cell_size)
        cell_y = nearest_cell_index(
            self.window.height - self._player.center_y,
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

        walls: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
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
