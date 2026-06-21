"""Lightweight game state model for runtime score/life tracking."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GameState:
    """Mutable per-run game state values used by gameplay systems."""

    score: int = 0
    pacgums_eaten: int = 0
    super_pacgums_eaten: int = 0

    def add_pacgum(self, points: int) -> None:
        """Increment score and regular pacgum counter."""
        self.score += max(0, points)
        self.pacgums_eaten += 1

    def add_super_pacgum(self, points: int) -> None:
        """Increment score and super pacgum counter."""
        self.score += max(0, points)
        self.super_pacgums_eaten += 1
