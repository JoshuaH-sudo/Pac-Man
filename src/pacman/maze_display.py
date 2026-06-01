"""Maze parsing and rendering primitives for the Arcade game view."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import arcade
from arcade.types import Color

from pacman.constants import (
    CLOSED_EAST,
    CLOSED_NORTH,
    CLOSED_SOUTH,
    CLOSED_WEST,
    COLLISION_WALL_THICKNESS_RATIO,
    MAZE_MARGIN,
    MAX_COLLISION_WALL_THICKNESS,
)
from pacman.types import GridPoint, WallCollider, WallSegment
from pacman.utils import normalize_segment


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
            raise ValueError("maze_grid must be a non-empty rectangular matrix")

        rows = len(maze_grid)
        cols = len(maze_grid[0])
        if any(len(row) != cols for row in maze_grid):
            raise ValueError("maze_grid rows must have equal length")

        points = tuple((x, y) for y in range(rows + 1) for x in range(cols + 1))
        wall_segments: set[WallSegment] = set()

        for y, row in enumerate(maze_grid):
            for x, cell in enumerate(row):
                cell_value = int(cell)
                if cell_value & CLOSED_NORTH:
                    wall_segments.add(normalize_segment((x, y), (x + 1, y)))
                if cell_value & CLOSED_EAST:
                    wall_segments.add(normalize_segment((x + 1, y), (x + 1, y + 1)))
                if cell_value & CLOSED_SOUTH:
                    wall_segments.add(normalize_segment((x, y + 1), (x + 1, y + 1)))
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
                        window_height - (offset_y + ((start_y + end_y) * cell_size / 2.0)),
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
