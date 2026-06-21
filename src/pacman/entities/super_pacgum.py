"""Super pacgum collectible entity."""

from __future__ import annotations

from pathlib import Path

from pacman.entities.entity import Entity

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "sprites"
SUPER_ITEM_SHEET_PATH = ASSETS_DIR / "super-pacgum.png"


class SuperPacgum(Entity):
    """Collectible super pacgum sprite with a looping 2x2 pulse animation."""

    POINT_VALUE = 50

    def __init__(
        self,
        center_x: float,
        center_y: float,
        scale: float = 1.0,
        animation_fps: float = 8.0,
    ) -> None:
        super().__init__(
            sprite_sheet_path=SUPER_ITEM_SHEET_PATH,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
        )
        self.define_animation(
            "pulse",
            [(0, 0), (0, 1), (1, 0), (1, 1)],
        )
        self.set_animation("pulse", reset=True)
        self._animation_interval = 1.0 / max(0.1, animation_fps)
        self._animation_elapsed = 0.0

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        self._animation_elapsed += delta_time
        if self._animation_elapsed < self._animation_interval:
            return

        self._animation_elapsed %= self._animation_interval
        self._advance_frame()
