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
            rows=4,
            columns=3,
        )
        self._speed = speed
        self._facing_animation = "right"
        self.define_animation("left", [(0, 0), (0, 1), (0, 2)])
        self.define_animation("right", [(1, 0), (1, 1), (1, 2)])
        self.define_animation("up", [(2, 0), (2, 1), (2, 2)])
        self.define_animation("down", [(3, 0), (3, 1), (3, 2)])
        self.set_animation(self._facing_animation, reset=True)

    @staticmethod
    def _animation_name_for_direction(horizontal: int, vertical: int) -> str | None:
        """Map movement direction to the matching sprite-sheet row."""
        if horizontal < 0:
            return "left"
        if horizontal > 0:
            return "right"
        if vertical > 0:
            return "up"
        if vertical < 0:
            return "down"
        return None

    def move(self, horizontal: int, vertical: int) -> None:
        """Set intended movement direction for the current update loop."""
        self.change_x = horizontal * self._speed
        self.change_y = vertical * self._speed
        next_animation = self._animation_name_for_direction(horizontal, vertical)
        if next_animation is not None:
            self._facing_animation = next_animation

    def set_speed(self, speed: float) -> None:
        """Update movement speed in pixels per frame."""
        self._speed = speed

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        del delta_time
        if self.change_x == 0 and self.change_y == 0:
            self.set_animation(self._facing_animation)
            return

        self.set_animation(self._facing_animation)
        self._advance_frame()
