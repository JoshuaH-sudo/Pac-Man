"""Shared Arcade sprite base entity for sheet-based game actors."""

from __future__ import annotations

from pathlib import Path

import arcade


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
