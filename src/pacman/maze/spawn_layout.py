"""Spawn and placement helpers for grid-aligned game entities."""

from __future__ import annotations

from typing import Sequence

from pacman.core import CLOSED_EAST, CLOSED_NORTH, CLOSED_SOUTH, CLOSED_WEST

FULLY_CLOSED_CELL_MASK = CLOSED_NORTH | CLOSED_EAST | CLOSED_SOUTH | CLOSED_WEST


def _is_corner_cell(cell_x: int, cell_y: int, cols: int, rows: int) -> bool:
    """Return True when a cell is one of the four maze corners."""
    max_cell_x = cols - 1
    max_cell_y = rows - 1
    return (cell_x in (0, max_cell_x)) and (cell_y in (0, max_cell_y))


def build_item_cells(
    maze_grid: Sequence[Sequence[int]],
) -> tuple[tuple[float, float], ...]:
    """Return Pacgum cells excluding maze corners and fully closed cells."""
    rows = len(maze_grid)
    cols = len(maze_grid[0])
    super_cells = {
        (int(cell_x), int(cell_y))
        for cell_x, cell_y in build_super_item_cells(maze_grid)
    }
    return tuple(
        (float(cell_x), float(cell_y))
        for cell_y, row in enumerate(maze_grid)
        for cell_x, cell_value in enumerate(row)
        if not _is_corner_cell(cell_x, cell_y, cols, rows)
        and (cell_x, cell_y) not in super_cells
        and (int(cell_value) & FULLY_CLOSED_CELL_MASK) != FULLY_CLOSED_CELL_MASK
    )


def build_super_item_cells(
    maze_grid: Sequence[Sequence[int]],
) -> tuple[tuple[float, float], ...]:
    """Return super pacgum cells matching ghost corner spawn positions."""
    rows = len(maze_grid)
    cols = len(maze_grid[0])
    return build_corner_cells(cols=cols, rows=rows)


def build_corner_cells(cols: int, rows: int) -> tuple[tuple[float, float], ...]:
    """Return the four maze corners in deterministic order."""
    max_cell_x = float(cols - 1)
    max_cell_y = float(rows - 1)
    return (
        (0.0, 0.0),
        (max_cell_x, 0.0),
        (0.0, max_cell_y),
        (max_cell_x, max_cell_y),
    )
