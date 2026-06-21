"""Spritesheet animation state and playback controller."""

from __future__ import annotations

from typing import Sequence

import arcade


class SpriteAnimation:
    """Manages named animation sequences and frame playback."""

    def __init__(
        self, textures: Sequence[arcade.Texture], rows: int, columns: int
    ) -> None:
        """Initialize animation controller with available textures and layout.

        Args:
            textures: List of arcade.Texture objects from spritesheet.
            rows: Number of rows in spritesheet grid.
            columns: Number of columns in spritesheet grid.
        """
        self._textures = textures
        self._rows = rows
        self._columns = columns
        self._animations: dict[str, tuple[int, ...]] = {
            "default": tuple(range(len(textures)))
        }
        self._active_animation_name = "default"
        self._active_animation_frame_offset = 0
        self._frame_index = 0

    @property
    def current_frame_index(self) -> int:
        """Return the current texture index."""
        return self._frame_index

    @property
    def current_texture(self) -> arcade.Texture:
        """Return the current texture object."""
        return self._textures[self._frame_index]

    def define_animation(
        self,
        name: str,
        frames: Sequence[int | tuple[int, int]],
    ) -> None:
        """Register a named animation from frame indices or (row, col) pairs.

        Args:
            name: Unique identifier for this animation.
            frames: Sequence of frame positions (flat indices or (row, col)).

        Raises:
            ValueError: If name is empty or frames is empty.
        """
        if not name:
            raise ValueError("animation name must not be empty")
        if not frames:
            raise ValueError("animation frames must not be empty")

        resolved_frames = tuple(self._resolve_frame_spec(frame) for frame in frames)
        self._animations[name] = resolved_frames

    def set_animation(self, name: str, reset: bool = False) -> None:
        """Activate a named animation; optionally restart at its first frame.

        Args:
            name: Animation name to activate.
            reset: Whether to restart the animation from frame 0.

        Raises:
            KeyError: If animation name does not exist.
        """
        if name not in self._animations:
            raise KeyError(f"unknown animation: {name}")

        if name != self._active_animation_name:
            self._active_animation_name = name
            reset = True

        if reset:
            self._active_animation_frame_offset = 0
            self._frame_index = self._animations[name][0]

    def set_animation_frame(self, name: str, offset: int = 0) -> None:
        """Set a named animation and force a specific frame offset.

        Args:
            name: Animation name to activate.
            offset: Frame offset within the animation sequence.

        Raises:
            KeyError: If animation name does not exist.
            ValueError: If frame offset is out of range.
        """
        if name not in self._animations:
            raise KeyError(f"unknown animation: {name}")

        frames = self._animations[name]
        if offset < 0 or offset >= len(frames):
            raise ValueError("animation frame offset out of range")

        self._active_animation_name = name
        self._active_animation_frame_offset = offset
        self._frame_index = frames[offset]

    def advance_frame(self) -> None:
        """Advance one frame in the active named animation sequence."""
        active_frames = self._animations[self._active_animation_name]
        self._active_animation_frame_offset = (
            self._active_animation_frame_offset + 1
        ) % len(active_frames)
        self._frame_index = active_frames[self._active_animation_frame_offset]

    def _resolve_frame_spec(self, frame: int | tuple[int, int]) -> int:
        """Resolve a flat index or (row, col) frame position to a flat index.

        Args:
            frame: Frame position as int or (row, col) tuple.

        Returns:
            Flat index into texture list.

        Raises:
            ValueError: If position is out of bounds.
        """
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
