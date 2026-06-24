"""Tests for Pac-Man config loading."""

from pathlib import Path
import pytest

from pacman.core import Parser


def test_load_config_supports_comments(tmp_path: Path) -> None:
    """The loader should ignore full-line comments in JSON files."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 5,\n  \"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    assert loaded.lives == 5
    assert loaded.points_per_ghost == 50


def test_invalid_keys_ignored(tmp_path: Path) -> None:
    """The loader should ignore invalid keys."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"lives1233\": 5,\n  \"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    assert loaded.lives == 3
    assert loaded.points_per_ghost == 50


def test_load_config_returns_defaults_on_missing_file(tmp_path: Path,
                                                      capsys: pytest.CaptureFixture[str]
                                                      ) -> None:
    """Missing files should return safe defaults."""
    parser = Parser(tmp_path / "does-not-exist.json")
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert len(loaded.levels) == 10
    assert loaded.highscore_filename == "highscores.json"
    assert "default" in out


def test_load_config_handles_unreadable_file(tmp_path: Path,
                                             monkeypatch: pytest.MonkeyPatch,
                                             capsys: pytest.CaptureFixture[str]
                                             ) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text('{"lives": 5}', encoding="utf-8")

    monkeypatch.setattr(
        Path,
        "read_text",
        lambda self, *args, **kwargs: (_ for _ in ()).throw(PermissionError("permission"
                                                                            "denied")),
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    assert loaded.lives == 3
    assert loaded.highscore_filename == "highscores.json"
    assert "ConfigError:" in capsys.readouterr().err


def test_invalid_json_file(tmp_path: Path,
                           capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "invalid.json"
    config_file.write_text(
        "# comment\n{\n  \"highscore_filename\": 5,\n  \"points_per_ghost\": 50\n\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert len(loaded.levels) == 10
    assert loaded.highscore_filename == "highscores.json"
    assert "default" in out


def test_invalid_highscore_file(tmp_path: Path,
                                capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"highscore_filename\": 5,\n  \"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert loaded.highscore_filename == "highscores.json"
    assert loaded.points_per_ghost == 50


def test_invalid_levels(tmp_path: Path,
                        capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"levels\": {},\n  \"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert len(loaded.levels) == 10
    assert loaded.levels == [(21, 21)] * 10
    assert loaded.points_per_ghost == 50


def test_invalid_level_dim(tmp_path: Path,
                           capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"levels\": [{\"width\": -234, \"height\": 0},"
        "{ \"width\": 21, \"height\": 21 },"
        "{ \"width\": 22, \"height\": 22 },"
        "{ \"width\": 23, \"height\": 23 },"
        "{ \"width\": 24, \"height\": 24 },"
        "{ \"width\": 25, \"height\": 25 },"
        "{ \"width\": 26, \"height\": 26 },"
        "{ \"width\": 27, \"height\": 27 },"
        "{ \"width\": 28, \"height\": 28 },"
        "{ \"width\": 29, \"height\": 29 }"
        "],\n "
        "\"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert len(loaded.levels) == 10
    assert loaded.levels[0] == (21, 21)
    assert loaded.levels[9] == (29, 29)
    assert loaded.points_per_ghost == 50


def test_at_least_10_levels(tmp_path: Path,
                            capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "config.json"
    config_file.write_text(
        "# comment\n{\n  \"levels\": [{\"width\": 20, \"height\": 20},"
        "{ \"width\": 21, \"height\": 21 },"
        "{ \"width\": 22, \"height\": 22 },"
        "{ \"width\": 23, \"height\": 23 },"
        "{ \"width\": 24, \"height\": 24 },"
        "{ \"width\": 25, \"height\": 25 },"
        "{ \"width\": 26, \"height\": 26 }"
        "],\n "
        "\"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert len(loaded.levels) == 10
    assert loaded.levels[0] == (20, 20)
    assert loaded.levels[9] == (21, 21)
    assert loaded.points_per_ghost == 50


def test_invalid_lives(tmp_path: Path,
                       capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "invalid-lives.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 0,\n  \"points_per_ghost\": 50\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert loaded.lives == 3
    assert loaded.highscore_filename == "highscores.json"
    assert loaded.points_per_ghost == 50


def test_invalid_pacgum(tmp_path: Path,
                        capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "invalid-lives.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 10,\n  \"pacgum\": \"vjhufsgh\"\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert loaded.lives == 10
    assert loaded.highscore_filename == "highscores.json"


def test_invalid_pacgum_point(tmp_path: Path,
                              capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "invalid-lives.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 10,\n  \"points_per_pacgum\": -9583\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert loaded.lives == 10
    assert loaded.highscore_filename == "highscores.json"
    assert loaded.points_per_pacgum == 10


def test_invalid_superpacgum(tmp_path: Path,
                             capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "invalid-lives.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 10,\n  \"points_per_super_pacgum\": \"fdsd\"\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert loaded.lives == 10
    assert loaded.highscore_filename == "highscores.json"
    assert loaded.points_per_super_pacgum == 50


def test_invalid_ghost_point(tmp_path: Path,
                             capsys: pytest.CaptureFixture[str]) -> None:
    config_file = tmp_path / "invalid-lives.json"
    config_file.write_text(
        "# comment\n{\n  \"lives\": 10,\n  \"points_per_ghost\": \"vjhufsgh\"\n}\n",
        encoding="utf-8",
    )

    parser = Parser(config_file)
    loaded = parser.load_config()

    out = capsys.readouterr().err
    assert "default" in out
    assert loaded.lives == 10
    assert loaded.highscore_filename == "highscores.json"
    assert loaded.points_per_ghost == 200
