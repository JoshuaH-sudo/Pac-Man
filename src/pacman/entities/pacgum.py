"""Pacgum collectible entity."""

from __future__ import annotations

from pathlib import Path

from pacman.entities.entity import Entity

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "sprites"
ITEM_SHEET_PATH = ASSETS_DIR / "pacgum.png"


class Pacgum(Entity):
    """Collectible regular pacgum sprite with no animation."""

    POINT_VALUE = 10

    def __init__(
        self,
        center_x: float,
        center_y: float,
        scale: float = 1.0,
    ) -> None:
        super().__init__(
            sprite_sheet_path=ITEM_SHEET_PATH,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
            rows=1,
            columns=1,
        )
