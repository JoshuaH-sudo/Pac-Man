"""Tests for highscore handling."""

from pathlib import Path

from pacman.highscore import (
    HighscoreEntry,
    HighScore
)


def test_sanitize_name_limits_format_and_length() -> None:
    """Names should stay compliant with project constraints."""
    assert HighScore.sanitize_name("Valid Name") == "Valid Name"
    assert HighScore.sanitize_name("name-with-symbol") == "PLAYER"
    assert HighScore.sanitize_name("ABCDEFGHIJKL") == "ABCDEFGHIJ"


def test_load_and_save_highscores_keep_top_ten(tmp_path: Path) -> None:
    """Persisted highscores should remain sorted and capped."""
    score_file = tmp_path / "scores.json"
    scores = [HighscoreEntry(name=f"P{i}", score=i) for i in range(20)]

    HighScore(score_file).save_highscores(scores)
    loaded = HighScore(score_file).load_highscores()

    assert len(loaded) == 10
    assert loaded[0].score == 19
    assert loaded[-1].score == 10
