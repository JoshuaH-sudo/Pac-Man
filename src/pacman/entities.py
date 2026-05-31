"""Game entities backed by 2x2 sprite sheet assets."""

from __future__ import annotations

from pathlib import Path

import arcade

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets" / "sprites"
PLAYER_SHEET_PATH = ASSETS_DIR / "pacman.png"
ITEM_SHEET_PATH = ASSETS_DIR / "pacgum.png"


def _load_2x2_textures(sheet_path: Path) -> list[arcade.Texture]:
    """Load four textures from a 2x2 sprite sheet."""
    sprite_sheet = arcade.load_spritesheet(sheet_path)
    frame_size = (
        sprite_sheet.image.width // 2,
        sprite_sheet.image.height // 2,
    )
    return sprite_sheet.get_texture_grid(
        size=frame_size,
        columns=2,
        count=4,
    )


class Item(arcade.Sprite):
    """Collectible pacgum sprite that loops through a 2x2 animation."""

    def __init__(self, center_x: float, center_y: float, scale: float = 1.0):
        textures = _load_2x2_textures(ITEM_SHEET_PATH)
        super().__init__(textures[0], scale=scale, center_x=center_x, center_y=center_y)
        self._textures = textures
        self._frame_index = 0

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        del delta_time
        self._frame_index = (self._frame_index + 1) % len(self._textures)
        self.texture = self._textures[self._frame_index]


class Player(arcade.Sprite):
    """Player-controlled Pac-Man sprite with 4-direction movement."""

    def __init__(
        self,
        center_x: float,
        center_y: float,
        speed: float,
        scale: float = 1.0,
    ):
        textures = _load_2x2_textures(PLAYER_SHEET_PATH)
        super().__init__(textures[0], scale=scale, center_x=center_x, center_y=center_y)
        self._textures = textures
        self._frame_index = 0
        self._speed = speed

    def move(self, horizontal: int, vertical: int) -> None:
        """Set intended movement direction for the current update loop."""
        self.change_x = horizontal * self._speed
        self.change_y = vertical * self._speed

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        del delta_time
        if self.change_x == 0 and self.change_y == 0:
            self.texture = self._textures[0]
            return

        self._frame_index = (self._frame_index + 1) % len(self._textures)
        self.texture = self._textures[self._frame_index]
