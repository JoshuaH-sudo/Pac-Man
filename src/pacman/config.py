"""Configuration loading helpers for Pac-Man."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class GameConfig:
    """Runtime configuration values with safe defaults."""

    highscore_filename: str = "highscores.json"
    levels: int = 10
    width: int = 21
    height: int = 21
    lives: int = 3
    pacgum: int = 42
    points_per_pacgum: int = 10
    points_per_super_pacgum: int = 50
    points_per_ghost: int = 200
    seed: int = 42
    level_max_time: int = 90


_DEFAULT_CONFIG = GameConfig()
_INT_FIELDS = {
    "levels",
    "width",
    "height",
    "lives",
    "pacgum",
    "points_per_pacgum",
    "points_per_super_pacgum",
    "points_per_ghost",
    "seed",
    "level_max_time",
}


def _strip_json_comments(content: str) -> str:
    """Return JSON-compatible content by skipping full-line comments."""
    kept_lines: list[str] = []
    for line in content.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        kept_lines.append(line)
    return "\n".join(kept_lines)


def _coerce_non_negative_int(value: Any, default: int) -> int:
    """Convert value into a non-negative integer fallbacking to default."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return max(0, value)
    return default


def _coerce_non_empty_str(value: Any, default: str) -> str:
    """Convert value into a non-empty stripped string fallbacking to default."""
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return default


def load_config(path: str | Path) -> GameConfig:
    """Load config from path while tolerating invalid values and comments."""
    config_path = Path(path)
    if not config_path.exists() or config_path.suffix.lower() != ".json":
        return GameConfig()

    try:
        content = config_path.read_text(encoding="utf-8")
        parsed = json.loads(_strip_json_comments(content))
    except (OSError, json.JSONDecodeError):
        return GameConfig()

    if not isinstance(parsed, dict):
        return GameConfig()

    merged: dict[str, Any] = {
        "highscore_filename": _DEFAULT_CONFIG.highscore_filename,
        "levels": _DEFAULT_CONFIG.levels,
        "width": _DEFAULT_CONFIG.width,
        "height": _DEFAULT_CONFIG.height,
        "lives": _DEFAULT_CONFIG.lives,
        "pacgum": _DEFAULT_CONFIG.pacgum,
        "points_per_pacgum": _DEFAULT_CONFIG.points_per_pacgum,
        "points_per_super_pacgum": _DEFAULT_CONFIG.points_per_super_pacgum,
        "points_per_ghost": _DEFAULT_CONFIG.points_per_ghost,
        "seed": _DEFAULT_CONFIG.seed,
        "level_max_time": _DEFAULT_CONFIG.level_max_time,
    }

    for key, value in parsed.items():
        if key in _INT_FIELDS:
            merged[key] = _coerce_non_negative_int(value, merged[key])
        elif key == "highscore_filename":
            merged[key] = _coerce_non_empty_str(value, merged[key])

    return GameConfig(**merged)
