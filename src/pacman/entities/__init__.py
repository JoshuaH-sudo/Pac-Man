"""Compatibility exports for split Pac-Man entity modules."""

from pacman.entities.entity import Entity
from pacman.entities.ghost import Ghost
from pacman.entities.pacgum import Pacgum
from pacman.entities.pacman import Pacman

# Backward-compatible aliases for existing imports.
Item = Pacgum
Player = Pacman

__all__ = [
    "Entity",
    "Ghost",
    "Pacman",
    "Pacgum",
    "Player",
    "Item",
]
