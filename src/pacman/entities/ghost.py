"""Ghost enemy entity."""

from __future__ import annotations

from pathlib import Path
import random

from pacman.entities.entity import Entity
from pacman.core import Direction, choose_initial_direction, direction_is_open

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "sprites"


class Ghost(Entity):
    """Simple ghost sprite with configurable sheet and movement speed."""

    def __init__(
        self,
        sprite_sheet_name: str,
        center_x: float,
        center_y: float,
        speed: float,
        scale: float = 1.0,
    ) -> None:
        super().__init__(
            sprite_sheet_path=ASSETS_DIR / sprite_sheet_name,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
            rows=2,
            columns=1,
        )
        self.define_animation("idle", [(0, 0)])
        self.define_animation("vulnerable", [(1, 0)])
        self.set_animation_frame("idle")

        self._speed = speed
        self._direction: Direction = (0, 0)
        self._is_vulnerable = False

    def set_vulnerable(self, is_vulnerable: bool) -> None:
        """Switch between idle and vulnerability ghost sprite rows."""
        if self._is_vulnerable == is_vulnerable:
            return

        self._is_vulnerable = is_vulnerable
        self.set_animation_frame("vulnerable" if is_vulnerable else "idle")

    def move(self, horizontal: int, vertical: int) -> None:
        """Set movement direction for the current update loop."""
        self.change_x = horizontal * self._speed
        self.change_y = vertical * self._speed

    def set_speed(self, speed: float) -> None:
        """Update movement speed in pixels per frame."""
        self._speed = speed

    def set_spawn_direction(self, cell_value: int) -> None:
        """Reset movement heading from the ghost's spawn cell exits."""
        self._direction = choose_initial_direction(cell_value)

    def update_maze_movement(
        self,
        cell_value: int,
        center_x: float,
        center_y: float,
        cell_size: float,
        offset_x: float,
        offset_y: float,
    ) -> None:
        """Resolve a ghost step with maze-aware turns and lane alignment."""
        open_directions = [
            direction
            for direction in ((0, 1), (1, 0), (0, -1), (-1, 0))
            if direction_is_open(cell_value, direction)
        ]
        if not open_directions:
            self._direction = (0, 0)
            self.move(0, 0)
            return

        alignment_tolerance = max(0.5, cell_size * 0.03)
        aligned_to_center = (
            abs(self.center_x - center_x) <= alignment_tolerance
            and abs(self.center_y - center_y) <= alignment_tolerance
        )

        if (
            self._direction != (0, 0)
            and not direction_is_open(cell_value, self._direction)
            and not aligned_to_center
        ):
            # When entering a corner cell, keep moving to its center before
            # changing heading; stopping early causes corner lockups.
            distance_to_center = 0.0
            if self._direction[0] != 0:
                distance_to_center = (center_x - self.center_x) * self._direction[0]
            elif self._direction[1] != 0:
                distance_to_center = (center_y - self.center_y) * self._direction[1]

            if distance_to_center > alignment_tolerance:
                self.move(self._direction[0], self._direction[1])
                self.snap_to_lane(
                    direction=self._direction,
                    cell_size=cell_size,
                    offset_x=offset_x,
                    offset_y=offset_y,
                    max_alignment_step=max(abs(self.change_x), abs(self.change_y)),
                )
                return

            self.center_x = center_x
            self.center_y = center_y
            aligned_to_center = True

        next_direction = self._direction
        if aligned_to_center:
            self.center_x = center_x
            self.center_y = center_y
            reverse_direction = (-self._direction[0], -self._direction[1])
            non_reverse_directions = [
                direction
                for direction in open_directions
                if direction != reverse_direction
            ]
            candidate_directions = (
                non_reverse_directions
                if non_reverse_directions
                else open_directions
            )
            if self._direction in candidate_directions and random.random() < 0.65:
                next_direction = self._direction
            else:
                next_direction = random.choice(candidate_directions)
        else:
            # Between centers, keep heading unchanged to avoid diagonal corner cuts.
            if self._direction not in open_directions:
                next_direction = (0, 0)

        if (
            next_direction != (0, 0)
            and not direction_is_open(cell_value, next_direction)
        ):
            next_direction = (0, 0)

        self._direction = next_direction
        self.move(next_direction[0], next_direction[1])
        self.snap_to_lane(
            direction=self._direction,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
            max_alignment_step=max(abs(self.change_x), abs(self.change_y)),
        )

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        """Ghost sprites are static for now; animation support comes later."""
        del delta_time
