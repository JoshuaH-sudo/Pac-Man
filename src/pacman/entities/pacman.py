"""Pac-Man player entity."""

from __future__ import annotations

from pathlib import Path

from pacman.entities.entity import Entity

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "sprites"
PLAYER_SHEET_PATH = ASSETS_DIR / "pacman.png"


class Pacman(Entity):
    """Player-controlled Pac-Man sprite with 4-direction movement."""

    def __init__(
        self,
        center_x: float,
        center_y: float,
        speed: float,
        scale: float = 1.0,
    ) -> None:
        super().__init__(
            sprite_sheet_path=PLAYER_SHEET_PATH,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
        )
        self._speed = speed

    def move(self, horizontal: int, vertical: int) -> None:
        """Set intended movement direction for the current update loop."""
        self.change_x = horizontal * self._speed
        self.change_y = vertical * self._speed

    def set_speed(self, speed: float) -> None:
        """Update movement speed in pixels per frame."""
        self._speed = speed

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        del delta_time
        if self.change_x == 0 and self.change_y == 0:
            self.texture = self._textures[0]
            return

        self._advance_frame()
