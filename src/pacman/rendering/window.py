"""Window bootstrap helpers for the Pac-Man game."""

from __future__ import annotations

import arcade

from pacman.core import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from pacman.core.config import GameConfig
from pacman.ui.main_menu import MainMenu


def create_game_window(
    config: GameConfig,
) -> arcade.Window:
    """Create the Arcade window, attach GameView, and return the window."""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    main_menu = MainMenu(config)
    window.show_view(main_menu)
    return window


__all__ = [
    "WINDOW_WIDTH",
    "WINDOW_HEIGHT",
    "WINDOW_TITLE",
    "create_game_window",
]
