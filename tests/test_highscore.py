"""Tests for highscore handling."""

from pathlib import Path

from pacman.highscore import (
    HighscoreEntry,
    load_highscores,
    sanitize_name,
    save_highscores,
)


def test_sanitize_name_limits_format_and_length() -> None:
    """Names should stay compliant with project constraints."""
    assert sanitize_name("Valid Name") == "Valid Name"
    assert sanitize_name("name-with-symbol") == "PLAYER"
    assert sanitize_name("ABCDEFGHIJKL") == "ABCDEFGHIJ"


def test_load_and_save_highscores_keep_top_ten(tmp_path: Path) -> None:
    """Persisted highscores should remain sorted and capped."""
    score_file = tmp_path / "scores.json"
    scores = [HighscoreEntry(name=f"P{i}", score=i) for i in range(20)]

    save_highscores(score_file, scores)
    loaded = load_highscores(score_file)

    assert len(loaded) == 10
    assert loaded[0].score == 19
    assert loaded[-1].score == 10
