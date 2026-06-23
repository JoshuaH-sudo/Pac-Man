"""Tests for runtime game state and score updates."""

from pacman.game import GameState
from pacman.core.config import GameConfig


config = GameConfig()


def test_add_pacgum_increments_score_and_counter() -> None:
    """Regular pacgum collection should increment score and normal count."""
    state = GameState(config)

    state.add_pacgum(10)

    assert state.score == 10
    assert state.pacgums_eaten == 1
    assert state.super_pacgums_eaten == 0


def test_add_super_pacgum_increments_score_and_counter() -> None:
    """Super pacgum collection should increment score and super count."""
    state = GameState(config)

    state.add_super_pacgum(50)

    assert state.score == 50
    assert state.pacgums_eaten == 0
    assert state.super_pacgums_eaten == 1


def test_negative_points_are_clamped_to_zero() -> None:
    """Defensive point updates should never reduce score by bad input."""
    state = GameState(config)

    state.score = 20
    state.add_pacgum(-100)
    state.add_super_pacgum(-50)

    assert state.score == 20
    assert state.pacgums_eaten == 1
    assert state.super_pacgums_eaten == 1
