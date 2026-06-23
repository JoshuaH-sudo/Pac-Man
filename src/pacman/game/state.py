"""Lightweight game state model for runtime score/life tracking."""

from __future__ import annotations

from dataclasses import dataclass

from pacman.core.config import GameConfig


@dataclass
class GameState:
    """Mutable per-run game state values used by gameplay systems."""

    def __init__(self, config: GameConfig) -> None:
        self.lives: int = config.lives
        self.level: int = 1
        self.score: int = 0
        self.pacgums_eaten: int = 0
        self.super_pacgums_eaten: int = 0
        self.timer: int = 0

    def add_pacgum(self, points: int) -> None:
        """Increment score and regular pacgum counter."""
        self.score += max(0, points)
        self.pacgums_eaten += 1

    def add_super_pacgum(self, points: int) -> None:
        """Increment score and super pacgum counter."""
        self.score += max(0, points)
        self.super_pacgums_eaten += 1

    def lose_life(self) -> None:
        self.lives -= 1

    def advance_level(self) -> None:
        self.level += 1
