"""Shared Arcade sprite base entity for sheet-based game actors."""

from __future__ import annotations

from pathlib import Path

import arcade

from pacman.entities.animation import SpriteAnimation
from pacman.entities.maze_movement import EntityMazeMovement
from pacman.types import Direction


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
        self._animation = SpriteAnimation(textures, rows, columns)
        self.texture = self._animation.current_texture

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

    def define_animation(
        self,
        name: str,
        frames: list[int | tuple[int, int]],
    ) -> None:
        """Register a named animation from frame indices or (row, col) pairs."""
        self._animation.define_animation(name, frames)

    def set_animation(self, name: str, reset: bool = False) -> None:
        """Activate a named animation; optionally restart at its first frame."""
        self._animation.set_animation(name, reset)
        self.texture = self._animation.current_texture

    def set_animation_frame(self, name: str, offset: int = 0) -> None:
        """Set a named animation and force a specific frame offset."""
        self._animation.set_animation_frame(name, offset)
        self.texture = self._animation.current_texture

    def _advance_frame(self) -> None:
        """Advance one frame in the active named animation sequence."""
        self._animation.advance_frame()
        self.texture = self._animation.current_texture

    def snap_to_lane(
        self,
        direction: Direction,
        cell_size: float,
        offset_x: float,
        offset_y: float,
        max_alignment_step: float | None = None,
    ) -> None:
        """Center the perpendicular axis to keep movement corridor-aligned."""
        self.center_x, self.center_y = (
            EntityMazeMovement.align_perpendicular_to_direction(
                self.center_x,
                self.center_y,
                direction,
                cell_size,
                offset_x,
                offset_y,
                max_alignment_step,
            )
        )

    def resolve_corner_turn(
        self,
        current_direction: Direction,
        desired_direction: Direction,
        cell_size: float,
        offset_x: float,
        offset_y: float,
    ) -> Direction:
        """Apply grid-aligned turn resolution and return the chosen direction."""
        next_direction, snapped_x, snapped_y = (
            EntityMazeMovement.resolve_direction_at_corner(
                current_direction=current_direction,
                desired_direction=desired_direction,
                current_x=self.center_x,
                current_y=self.center_y,
                cell_size=cell_size,
                offset_x=offset_x,
                offset_y=offset_y,
            )
        )
        self.center_x = snapped_x
        self.center_y = snapped_y
        return next_direction
