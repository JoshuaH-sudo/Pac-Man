"""Ghost enemy entity."""

from __future__ import annotations

from pathlib import Path

from pacman.entities.entity import Entity

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
            rows=1,
            columns=1,
        )
        self._speed = speed

    def move(self, horizontal: int, vertical: int) -> None:
        """Set movement direction for the current update loop."""
        self.change_x = horizontal * self._speed
        self.change_y = vertical * self._speed

    def set_speed(self, speed: float) -> None:
        """Update movement speed in pixels per frame."""
        self._speed = speed

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        """Ghost sprites are static for now; animation support comes later."""
        del delta_time
