"""Window bootstrap helpers for the Pac-Man game."""

from __future__ import annotations

import arcade

from pacman.core import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from pacman.core.config import GameConfig
from pacman.game import GameView


def create_game_window(
    maze_grid: list[list[int]] | tuple[tuple[int, ...], ...],
    config: GameConfig,
) -> arcade.Window:
    """Create the Arcade window, attach GameView, and return the window."""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game = GameView(maze_grid, config)
    window.show_view(game)
    return window


__all__ = [
    "WINDOW_WIDTH",
    "WINDOW_HEIGHT",
    "WINDOW_TITLE",
    "create_game_window",
]
