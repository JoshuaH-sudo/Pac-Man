"""Tests for Pac-Man config loading."""

from pathlib import Path

from pacman.config import load_config


def test_load_config_supports_comments(tmp_path: Path) -> None:
    """The loader should ignore full-line comments in JSON files."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 5,\n  \"points_per_ghost\": -50\n}\n",
        encoding="utf-8",
    )

    loaded = load_config(config_file)

    assert loaded.lives == 5
    assert loaded.points_per_ghost == 0


def test_load_config_returns_defaults_on_missing_file(tmp_path: Path) -> None:
    """Missing files should return safe defaults."""
    loaded = load_config(tmp_path / "does-not-exist.json")
    assert loaded.levels == 10
    assert loaded.highscore_filename == "highscores.json"
