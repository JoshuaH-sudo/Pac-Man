"""Arcade window and maze rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import arcade
from arcade.types import Color

from pacman.entities import Item, Player

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
WINDOW_TITLE = "Pac-Man"

CLOSED_NORTH = 0b0001
CLOSED_EAST = 0b0010
CLOSED_SOUTH = 0b0100
CLOSED_WEST = 0b1000

PLAYER_MOVEMENT_SPEED = 10

GridPoint = tuple[int, int]
WallSegment = tuple[GridPoint, GridPoint]


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
                    wall_segments.add(_normalize_segment((x, y), (x + 1, y)))
                if cell_value & CLOSED_EAST:
                    wall_segments.add(
                        _normalize_segment((x + 1, y), (x + 1, y + 1))
                    )
                if cell_value & CLOSED_SOUTH:
                    wall_segments.add(
                        _normalize_segment((x, y + 1), (x + 1, y + 1))
                    )
                if cell_value & CLOSED_WEST:
                    wall_segments.add(_normalize_segment((x, y), (x, y + 1)))

        return cls(
            rows=rows,
            cols=cols,
            points=points,
            wall_segments=tuple(sorted(wall_segments)),
        )


def _normalize_segment(start: GridPoint, end: GridPoint) -> WallSegment:
    """Keep segment ordering stable so duplicate walls collapse into one."""
    return (start, end) if start <= end else (end, start)


class MazeDisplay:
    """Render maze walls from a point-grid onto an Arcade view."""

    def __init__(
        self,
        maze_grid: Sequence[Sequence[int]],
        margin: float = 40.0,
        wall_color: Color = arcade.color.ALICE_BLUE,
        wall_width: float = 2.0,
    ) -> None:
        self._point_grid = MazePointGrid.from_maze_grid(maze_grid)
        self._margin = margin
        self._wall_color = wall_color
        self._wall_width = wall_width

    def draw(self, window_width: int, window_height: int) -> None:
        """Draw all closed walls scaled to the current window size."""
        cell_size, offset_x, offset_y = self._fit_to_window(
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

    def _fit_to_window(
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


class GameView(arcade.View):
    """Main game view that currently renders the generated maze walls."""

    def __init__(self, maze_grid: Sequence[Sequence[int]]):
        super().__init__()
        self._maze_display = MazeDisplay(maze_grid)
        self._player = Player(
            center_x=WINDOW_WIDTH / 2,
            center_y=WINDOW_HEIGHT / 2,
            speed=PLAYER_MOVEMENT_SPEED,
            scale=2.0,
        )
        self._players: arcade.SpriteList = arcade.SpriteList()
        self._players.append(self._player)

        self._items: arcade.SpriteList = arcade.SpriteList()
        self._items.append(
            Item(
                center_x=(WINDOW_WIDTH / 2) + 96,
                center_y=(WINDOW_HEIGHT / 2) + 96,
                scale=1.5,
            )
        )

        self._move_left = False
        self._move_right = False
        self._move_up = False
        self._move_down = False

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)

    def on_draw(self) -> None:
        self.clear()
        self._maze_display.draw(self.window.width, self.window.height)
        self._items.draw()
        self._players.draw()

    def on_update(self, delta_time: float) -> None:
        del delta_time
        self._apply_player_movement()
        self._players.update()
        self._players.update_animation()
        self._items.update_animation()
        self._keep_player_on_screen()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        if symbol in (arcade.key.LEFT, arcade.key.A):
            self._move_left = True
        if symbol in (arcade.key.RIGHT, arcade.key.D):
            self._move_right = True
        if symbol in (arcade.key.UP, arcade.key.W):
            self._move_up = True
        if symbol in (arcade.key.DOWN, arcade.key.S):
            self._move_down = True

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        del modifiers
        if symbol in (arcade.key.LEFT, arcade.key.A):
            self._move_left = False
        if symbol in (arcade.key.RIGHT, arcade.key.D):
            self._move_right = False
        if symbol in (arcade.key.UP, arcade.key.W):
            self._move_up = False
        if symbol in (arcade.key.DOWN, arcade.key.S):
            self._move_down = False

    def _apply_player_movement(self) -> None:
        horizontal = int(self._move_right) - int(self._move_left)
        vertical = int(self._move_up) - int(self._move_down)
        self._player.move(horizontal=horizontal, vertical=vertical)

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
