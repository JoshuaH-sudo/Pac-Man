"""Player movement controller responsible for input buffering and lane alignment."""

from __future__ import annotations

import arcade

from pacman.types import Direction
from pacman.utils import (
    coerce_blocked_directions,
    direction_is_open,
    nearest_cell_center,
    resolve_player_direction,
)


class MovementController:
    """Encapsulates Pac-Man movement state and update logic."""

    def __init__(self, initial_direction: Direction) -> None:
        self._current_direction = initial_direction
        self._desired_direction = initial_direction
        self._queued_direction: Direction = (0, 0)
        self._lock_movement_for_spawn = True

    @property
    def current_direction(self) -> Direction:
        """Current active movement direction."""
        return self._current_direction

    def debug_state(self) -> tuple[Direction, Direction, Direction, bool]:
        """Return internal movement state for instrumentation/debug logs."""
        return (
            self._current_direction,
            self._desired_direction,
            self._queued_direction,
            self._lock_movement_for_spawn,
        )

    def reset(self, initial_direction: Direction) -> None:
        """Reset movement state after spawn sync/resizing."""
        self._current_direction = initial_direction
        self._desired_direction = initial_direction
        self._queued_direction = (0, 0)
        self._lock_movement_for_spawn = True

    def queue_input(self, symbol: int, cell_value: int | None = None) -> None:
        """Queue requested direction and accept immediately when valid."""
        next_direction: Direction | None = None
        if symbol in (arcade.key.LEFT, arcade.key.A):
            next_direction = (-1, 0)
        if symbol in (arcade.key.RIGHT, arcade.key.D):
            next_direction = (1, 0)
        if symbol in (arcade.key.UP, arcade.key.W):
            next_direction = (0, 1)
        if symbol in (arcade.key.DOWN, arcade.key.S):
            next_direction = (0, -1)

        if next_direction is None:
            return

        self._queued_direction = next_direction
        if cell_value is not None and direction_is_open(
            cell_value, self._queued_direction
        ):
            self._desired_direction = self._queued_direction
            self._queued_direction = (0, 0)

    def apply(
        self,
        player_center_x: float,
        player_center_y: float,
        cell_size: float,
        offset_x: float,
        offset_y: float,
        cell_value: int,
    ) -> tuple[Direction, float, float, bool]:
        """Compute movement direction and snapped position for this frame."""
        if self._lock_movement_for_spawn:
            self._lock_movement_for_spawn = False
            return (0, 0), player_center_x, player_center_y, True

        if self._queued_direction != (0, 0):
            if direction_is_open(cell_value, self._queued_direction):
                self._desired_direction = self._queued_direction
                self._queued_direction = (0, 0)

        self._current_direction, self._desired_direction = coerce_blocked_directions(
            self._current_direction,
            self._desired_direction,
            cell_value,
        )

        self._current_direction, center_x, center_y = resolve_player_direction(
            self._current_direction,
            self._desired_direction,
            player_center_x,
            player_center_y,
            cell_size,
            offset_x,
            offset_y,
        )
        return self._current_direction, center_x, center_y, False

    def snap_to_lane(
        self,
        player_center_x: float,
        player_center_y: float,
        cell_size: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[float, float]:
        """Snap perpendicular axis to nearest lane center."""
        center_x = player_center_x
        center_y = player_center_y
        if self._current_direction[0] != 0:
            center_y = nearest_cell_center(player_center_y, offset_y, cell_size)
        elif self._current_direction[1] != 0:
            center_x = nearest_cell_center(player_center_x, offset_x, cell_size)
        return center_x, center_y
