"""Shared Arcade sprite base entity for sheet-based game actors."""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

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
        self._rows = rows
        self._columns = columns
        self._textures = textures
        self._frame_index = 0
        self._animations: dict[str, tuple[int, ...]] = {
            "default": tuple(range(len(textures)))
        }
        self._active_animation_name = "default"
        self._active_animation_frame_offset = 0

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
        """Advance one frame in the active named animation sequence."""
        active_frames = self._animations[self._active_animation_name]
        self._active_animation_frame_offset = (
            self._active_animation_frame_offset + 1
        ) % len(active_frames)
        self._frame_index = active_frames[self._active_animation_frame_offset]
        self.texture = self._textures[self._frame_index]

    def define_animation(
        self,
        name: str,
        frames: Sequence[int | tuple[int, int]],
    ) -> None:
        """Register a named animation from frame indices or (row, col) pairs."""
        if not name:
            raise ValueError("animation name must not be empty")
        if not frames:
            raise ValueError("animation frames must not be empty")

        resolved_frames = tuple(self._resolve_frame_spec(frame) for frame in frames)
        self._animations[name] = resolved_frames

    def set_animation(self, name: str, reset: bool = False) -> None:
        """Activate a named animation; optionally restart at its first frame."""
        if name not in self._animations:
            raise KeyError(f"unknown animation: {name}")

        if name != self._active_animation_name:
            self._active_animation_name = name
            reset = True

        if reset:
            self._active_animation_frame_offset = 0
            self._frame_index = self._animations[name][0]
            self.texture = self._textures[self._frame_index]

    def set_animation_frame(self, name: str, offset: int = 0) -> None:
        """Set a named animation and force a specific frame offset."""
        if name not in self._animations:
            raise KeyError(f"unknown animation: {name}")

        frames = self._animations[name]
        if offset < 0 or offset >= len(frames):
            raise ValueError("animation frame offset out of range")

        self._active_animation_name = name
        self._active_animation_frame_offset = offset
        self._frame_index = frames[offset]
        self.texture = self._textures[self._frame_index]

    def _resolve_frame_spec(self, frame: int | tuple[int, int]) -> int:
        """Resolve a flat index or (row, col) frame position to a flat index."""
        if isinstance(frame, int):
            if frame < 0 or frame >= len(self._textures):
                raise ValueError("frame index out of range")
            return frame

        row, col = frame
        if row < 0 or row >= self._rows:
            raise ValueError("animation row out of range")
        if col < 0 or col >= self._columns:
            raise ValueError("animation column out of range")

        return row * self._columns + col

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
