"""Utility functions shared by maze parsing and player movement modules."""

from __future__ import annotations

from pacman.constants import (
    CLOSED_EAST,
    CLOSED_NORTH,
    CLOSED_SOUTH,
    CLOSED_WEST,
)
from pacman.types import Direction, GridPoint, WallSegment


def normalize_segment(start: GridPoint, end: GridPoint) -> WallSegment:
    """Keep segment ordering stable so duplicate walls collapse into one."""
    return (start, end) if start <= end else (end, start)


def center_cell_index(cell_count: int) -> int:
    """Return the nearest discrete center cell index for a maze axis."""
    return max(0, (cell_count - 1) // 2)


def direction_is_open(cell_value: int, direction: Direction) -> bool:
    """Return whether a maze cell allows travel in the given direction."""
    if direction == (0, 1):
        return not bool(cell_value & CLOSED_NORTH)
    if direction == (1, 0):
        return not bool(cell_value & CLOSED_EAST)
    if direction == (0, -1):
        return not bool(cell_value & CLOSED_SOUTH)
    if direction == (-1, 0):
        return not bool(cell_value & CLOSED_WEST)
    return False


def choose_initial_direction(cell_value: int) -> Direction:
    """Pick the first open direction in reading order for a maze cell."""
    if direction_is_open(cell_value, (0, 1)):
        return (0, 1)
    if direction_is_open(cell_value, (1, 0)):
        return (1, 0)
    if direction_is_open(cell_value, (-1, 0)):
        return (-1, 0)
    if direction_is_open(cell_value, (0, -1)):
        return (0, -1)
    return (0, 0)


def nearest_cell_index(
    coordinate: float,
    offset: float,
    cell_size: float,
) -> int:
    """Return the nearest maze cell index for a screen axis."""
    return int(round((coordinate - offset) / cell_size - 0.5))


def nearest_cell_center(
    coordinate: float,
    offset: float,
    cell_size: float,
) -> float:
    """Return the nearest maze cell center coordinate for a screen axis."""
    cell_index = nearest_cell_index(coordinate, offset, cell_size)
    return offset + (cell_index + 0.5) * cell_size


def resolve_player_direction(
    current_direction: Direction,
    desired_direction: Direction,
    center_x: float,
    center_y: float,
    cell_size: float,
    offset_x: float,
    offset_y: float,
) -> tuple[Direction, float, float]:
    """Keep travel axis-aligned and snap turns onto the cell grid."""
    alignment_tolerance = max(1.0, cell_size * 0.25)
    next_direction = (
        current_direction
        if current_direction != (0, 0)
        else desired_direction
    )
    snapped_x = center_x
    snapped_y = center_y

    if next_direction[0] != 0:
        lane_y = nearest_cell_center(center_y, offset_y, cell_size)
        if abs(center_y - lane_y) <= alignment_tolerance:
            snapped_y = lane_y
            if desired_direction[1] != 0:
                turn_x = nearest_cell_center(center_x, offset_x, cell_size)
                if abs(center_x - turn_x) <= alignment_tolerance:
                    snapped_x = turn_x
                    next_direction = desired_direction
            elif desired_direction[0] != 0:
                next_direction = desired_direction

    elif next_direction[1] != 0:
        lane_x = nearest_cell_center(center_x, offset_x, cell_size)
        if abs(center_x - lane_x) <= alignment_tolerance:
            snapped_x = lane_x
            if desired_direction[0] != 0:
                turn_y = nearest_cell_center(center_y, offset_y, cell_size)
                if abs(center_y - turn_y) <= alignment_tolerance:
                    snapped_y = turn_y
                    next_direction = desired_direction
            elif desired_direction[1] != 0:
                next_direction = desired_direction

    return next_direction, snapped_x, snapped_y


def coerce_blocked_directions(
    current_direction: Direction,
    desired_direction: Direction,
    cell_value: int,
) -> tuple[Direction, Direction]:
    """Stop movement when blocked and keep only immediately valid directions."""
    next_current = current_direction
    next_desired = desired_direction

    if next_current != (0, 0) and not direction_is_open(cell_value, next_current):
        next_current = (0, 0)
        next_desired = (0, 0)

    if next_current == (0, 0) and next_desired != (0, 0):
        if not direction_is_open(cell_value, next_desired):
            next_desired = (0, 0)

    return next_current, next_desired
