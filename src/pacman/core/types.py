"""Shared type aliases for Pac-Man maze and movement modules."""

from __future__ import annotations

GridPoint = tuple[int, int]
WallSegment = tuple[GridPoint, GridPoint]
WallCollider = tuple[float, float, float, float]
Direction = tuple[int, int]
