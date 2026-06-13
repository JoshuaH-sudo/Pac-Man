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
        max_alignment_step: float | None = None,
    ) -> tuple[float, float]:
        """Snap perpendicular axis to nearest lane center."""
        center_x = player_center_x
        center_y = player_center_y
        alignment_step = (
            max(1.0, cell_size / 8.0)
            if max_alignment_step is None
            else max(0.0, max_alignment_step)
        )

        def _step_toward(value: float, target: float) -> float:
            delta = target - value
            if abs(delta) <= alignment_step:
                return target
            return value + alignment_step * (1 if delta > 0 else -1)

        # Keep the non-travel axis centered so sprite movement stays visually
        # locked to corridors despite floating-point drift.
        if self._current_direction[0] != 0:
            lane_y = nearest_cell_center(player_center_y, offset_y, cell_size)
            center_y = _step_toward(player_center_y, lane_y)
        elif self._current_direction[1] != 0:
            lane_x = nearest_cell_center(player_center_x, offset_x, cell_size)
            center_x = _step_toward(player_center_x, lane_x)
        return center_x, center_y
