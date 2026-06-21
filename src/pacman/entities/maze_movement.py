"""Shared maze-aware movement controller for entities."""

from __future__ import annotations

from pacman.types import Direction
from pacman.utils import nearest_cell_center, resolve_direction


class EntityMazeMovement:
    """Handles maze-aware positioning and lane alignment for entities."""

    @staticmethod
    def interpolate_toward(
        value: float, target: float, max_step: float
    ) -> float:
        """Move a coordinate toward a target without overshooting.

        Args:
            value: Current coordinate value.
            target: Target coordinate value.
            max_step: Maximum distance to move in this step.

        Returns:
            New coordinate value, moved toward target by at most max_step.
        """
        delta = target - value
        if abs(delta) <= max_step:
            return target
        return value + max_step * (1 if delta > 0 else -1)

    @staticmethod
    def align_perpendicular_to_direction(
        current_x: float,
        current_y: float,
        direction: Direction,
        cell_size: float,
        offset_x: float,
        offset_y: float,
        max_alignment_step: float | None = None,
    ) -> tuple[float, float]:
        """Center the perpendicular axis to keep movement corridor-aligned.

        When moving in a direction, keep the non-travel axis centered on its
        lane to prevent drift and maintain grid-aligned movement appearance.

        Args:
            current_x: Current X position.
            current_y: Current Y position.
            direction: Active movement direction (dx, dy).
            cell_size: Size of maze cells in pixels.
            offset_x: X offset of maze in screen space.
            offset_y: Y offset of maze in screen space.
            max_alignment_step: Max pixels to step per call (default: cell_size/8).

        Returns:
            Tuple of (aligned_x, aligned_y).
        """
        alignment_step = (
            max(1.0, cell_size / 8.0)
            if max_alignment_step is None
            else max(0.0, max_alignment_step)
        )

        aligned_x = current_x
        aligned_y = current_y

        if direction[0] != 0:
            lane_y = nearest_cell_center(current_y, offset_y, cell_size)
            aligned_y = EntityMazeMovement.interpolate_toward(
                current_y, lane_y, alignment_step
            )
        elif direction[1] != 0:
            lane_x = nearest_cell_center(current_x, offset_x, cell_size)
            aligned_x = EntityMazeMovement.interpolate_toward(
                current_x, lane_x, alignment_step
            )

        return aligned_x, aligned_y

    @staticmethod
    def resolve_direction_at_corner(
        current_direction: Direction,
        desired_direction: Direction,
        current_x: float,
        current_y: float,
        cell_size: float,
        offset_x: float,
        offset_y: float,
    ) -> tuple[Direction, float, float]:
        """Apply grid-aligned turn resolution and return chosen direction.

        Handles smooth turns at maze corners by allowing direction changes
        when sufficiently aligned to a lane and approaching a turn point.

        Args:
            current_direction: Active movement direction.
            desired_direction: Intended next direction (from input or AI).
            current_x: Current X position.
            current_y: Current Y position.
            cell_size: Size of maze cells in pixels.
            offset_x: X offset of maze in screen space.
            offset_y: Y offset of maze in screen space.

        Returns:
            Tuple of (next_direction, snapped_x, snapped_y).
        """
        next_direction, snapped_x, snapped_y = resolve_direction(
            current_direction=current_direction,
            desired_direction=desired_direction,
            center_x=current_x,
            center_y=current_y,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        return next_direction, snapped_x, snapped_y
