"""Shared Arcade sprite base entity for sheet-based game actors."""

from __future__ import annotations

from pathlib import Path

import arcade

from pacman.types import Direction
from pacman.utils import nearest_cell_center, resolve_player_direction


class Entity(arcade.Sprite):
    """Base sprite entity that handles spritesheet texture management."""

    def __init__(
        self,
        sprite_sheet_path: Path,
        center_x: float,
        center_y: float,
        scale: float = 1.0,
        rows: int = 2,
        columns: int = 2,
    ) -> None:
        textures = self._load_textures(
            sprite_sheet_path,
            rows=rows,
            columns=columns,
        )
        super().__init__(
            textures[0],
            scale=scale,
            center_x=center_x,
            center_y=center_y,
        )
        self._textures = textures
        self._frame_index = 0

    @staticmethod
    def _load_textures(
        sheet_path: Path, rows: int = 2, columns: int = 2
    ) -> list[arcade.Texture]:
        """Load textures from a sprite sheet."""
        if rows <= 0 or columns <= 0:
            raise ValueError("rows and columns must be positive integers")

        sprite_sheet = arcade.load_spritesheet(sheet_path)
        frame_size = (
            sprite_sheet.image.width // columns,
            sprite_sheet.image.height // rows,
        )
        return sprite_sheet.get_texture_grid(
            size=frame_size,
            columns=columns,
            count=rows * columns,
        )

    def _advance_frame(self) -> None:
        """Advance to the next texture frame in a looping sequence."""
        self._frame_index = (self._frame_index + 1) % len(self._textures)
        self.texture = self._textures[self._frame_index]

    @staticmethod
    def _step_toward(value: float, target: float, max_step: float) -> float:
        """Move a coordinate toward a target without overshooting."""
        delta = target - value
        if abs(delta) <= max_step:
            return target
        return value + max_step * (1 if delta > 0 else -1)

    def snap_to_lane(
        self,
        direction: Direction,
        cell_size: float,
        offset_x: float,
        offset_y: float,
        max_alignment_step: float | None = None,
    ) -> None:
        """Center the perpendicular axis to keep movement corridor-aligned."""
        alignment_step = (
            max(1.0, cell_size / 8.0)
            if max_alignment_step is None
            else max(0.0, max_alignment_step)
        )

        if direction[0] != 0:
            lane_y = nearest_cell_center(self.center_y, offset_y, cell_size)
            self.center_y = self._step_toward(self.center_y, lane_y, alignment_step)
        elif direction[1] != 0:
            lane_x = nearest_cell_center(self.center_x, offset_x, cell_size)
            self.center_x = self._step_toward(self.center_x, lane_x, alignment_step)

    def resolve_corner_turn(
        self,
        current_direction: Direction,
        desired_direction: Direction,
        cell_size: float,
        offset_x: float,
        offset_y: float,
    ) -> Direction:
        """Apply grid-aligned turn resolution and return the chosen direction."""
        next_direction, snapped_x, snapped_y = resolve_player_direction(
            current_direction=current_direction,
            desired_direction=desired_direction,
            center_x=self.center_x,
            center_y=self.center_y,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
        )
        self.center_x = snapped_x
        self.center_y = snapped_y
        return next_direction
