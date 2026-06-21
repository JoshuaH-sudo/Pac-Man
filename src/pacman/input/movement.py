"""Player movement controller responsible for input buffering and lane alignment."""

from __future__ import annotations

import arcade

from pacman.core import Direction
from pacman.core import (
    coerce_blocked_directions,
    direction_is_open,
    nearest_cell_center,
    resolve_direction,
)


class MovementController:
    """Encapsulates Pac-Man movement state and update logic."""

    def __init__(self, initial_direction: Direction) -> None:
        # Track three direction intents separately:
        # current = what is moving now, desired = next valid heading,
        # queued = last player keypress waiting for an opening.
        self._current_direction = initial_direction
        self._desired_direction = initial_direction
        self._queued_direction: Direction = (0, 0)
        # Prevent one-frame drift before the player is fully synced to spawn.
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

        # Always remember the latest intent so turns can happen at junctions
        # even if the direction is currently blocked.
        self._queued_direction = next_direction
        if cell_value is not None and direction_is_open(
            cell_value, self._queued_direction
        ):
            # If already legal in the current cell, switch intent right away
            # for responsive controls.
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
            # First post-spawn frame is intentionally still; caller can use the
            # returned flag to avoid processing regular movement effects.
            self._lock_movement_for_spawn = False
            return (0, 0), player_center_x, player_center_y, True

        if self._queued_direction != (0, 0):
            if direction_is_open(cell_value, self._queued_direction):
                # Consume buffered input the moment that direction becomes open.
                self._desired_direction = self._queued_direction
                self._queued_direction = (0, 0)

        # When a direction is blocked in the current cell (e.g. dead-end exit),
        # do not stop immediately at cell-boundary rounding. Keep moving until
        # we reach the center stop point of the dead-end cell.
        if (
            self._current_direction != (0, 0)
            and not direction_is_open(cell_value, self._current_direction)
        ):
            stop_x = nearest_cell_center(player_center_x, offset_x, cell_size)
            stop_y = nearest_cell_center(player_center_y, offset_y, cell_size)
            stop_tolerance = max(1.0, cell_size * 0.1)

            distance_to_stop = 0.0
            approach_x = player_center_x
            approach_y = player_center_y
            if self._current_direction[0] != 0:
                distance_to_stop = (
                    (stop_x - player_center_x) * self._current_direction[0]
                )
                # Keep horizontal motion continuous; only align to the current lane.
                approach_y = nearest_cell_center(player_center_y, offset_y, cell_size)
            elif self._current_direction[1] != 0:
                distance_to_stop = (
                    (stop_y - player_center_y) * self._current_direction[1]
                )
                # Keep vertical motion continuous; only align to the current lane.
                approach_x = nearest_cell_center(player_center_x, offset_x, cell_size)

            if distance_to_stop > stop_tolerance:
                return self._current_direction, approach_x, approach_y, False

            self._current_direction = (0, 0)
            if (
                self._desired_direction != (0, 0)
                and direction_is_open(cell_value, self._desired_direction)
            ):
                # At corner centers, immediately apply a valid queued turn
                # instead of clearing it and getting stuck.
                self._current_direction = self._desired_direction
            elif (
                self._desired_direction != (0, 0)
                and not direction_is_open(cell_value, self._desired_direction)
            ):
                self._desired_direction = (0, 0)
            return self._current_direction, stop_x, stop_y, False

        previous_direction = self._current_direction
        self._current_direction, self._desired_direction = coerce_blocked_directions(
            self._current_direction,
            self._desired_direction,
            cell_value,
        )

        if previous_direction != (0, 0) and self._current_direction == (0, 0):
            # When movement is interrupted by a wall, snap to grid center to
            # prevent accumulating half-cell offsets over repeated collisions.
            center_x = nearest_cell_center(player_center_x, offset_x, cell_size)
            center_y = nearest_cell_center(player_center_y, offset_y, cell_size)
            return self._current_direction, center_x, center_y, False

        # Resolve legal turns and axis alignment while preserving smooth motion.
        self._current_direction, center_x, center_y = resolve_direction(
            self._current_direction,
            self._desired_direction,
            player_center_x,
            player_center_y,
            cell_size,
            offset_x,
            offset_y,
        )
        return self._current_direction, center_x, center_y, False
