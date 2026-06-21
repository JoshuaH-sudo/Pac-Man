"""Compatibility exports for split Pac-Man entity modules."""

from pacman.entities.entity import Entity
from pacman.entities.ghost import Ghost
from pacman.entities.pacgum import Pacgum
from pacman.entities.pacman import Pacman
from pacman.entities.super_pacgum import SuperPacgum

# Backward-compatible aliases for existing imports.
Item = Pacgum
Player = Pacman

__all__ = [
    "Entity",
    "Ghost",
    "Pacman",
    "Pacgum",
    "SuperPacgum",
    "Player",
    "Item",
]
