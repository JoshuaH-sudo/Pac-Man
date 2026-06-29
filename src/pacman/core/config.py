"""Configuration loading helpers for Pac-Man."""

from __future__ import annotations

import json
from pathlib import Path
from pydantic import BaseModel, Field, model_validator, ValidationError
import sys
from typing import Any


_DEFAULT_LEVEL_WIDTH = 14
_DEFAULT_LEVEL_HEIGHT = 14
_MIN_LEVELS = 10


class GameConfig(BaseModel):
    """Runtime configuration values with safe defaults."""

    highscore_filename: str = Field(default="highscores.json", min_length=6)
    levels: list[tuple[int, int]] = Field(
        default=[(_DEFAULT_LEVEL_WIDTH, _DEFAULT_LEVEL_HEIGHT)] * _MIN_LEVELS)
    lives: int = Field(default=3, gt=0)
    points_per_pacgum: int = Field(default=10, ge=0)
    points_per_super_pacgum: int = Field(default=50, ge=0)
    points_per_ghost: int = Field(default=200, ge=0)
    ghost_respawn_delay_seconds: int = Field(default=5, ge=0)
    seed: int = Field(default=42)
    level_max_time: int = Field(default=90, gt=0)

    @model_validator(mode="after")
    def post_validate(self) -> "GameConfig":
        if not self.highscore_filename.endswith(".json"):
            raise ValueError("Highscore file has to be a JSON file.")

        for i, (x, y) in enumerate(self.levels):
            if x < 1:
                raise ValueError(f"Invalid maze width for level {i + 1}. "
                                 "Maze width needs to be a positive integer.")
            if y < 1:
                raise ValueError(f"Invalid maze height for level {i + 1}. "
                                 "Maze width needs to be a positive integer.")

        if len(self.levels) < _MIN_LEVELS:
            raise ValueError(f"There must be at least {_MIN_LEVELS} levels.")

        return self


_DEFAULT_CONFIG = GameConfig()
_INT_FIELDS = {
    "lives",
    "points_per_pacgum",
    "points_per_super_pacgum",
    "points_per_ghost",
    "ghost_respawn_delay_seconds",
    "level_max_time",
    "seed"
}


class Parser:
    """Parse the config.json file and store in GameConfig."""
    def __init__(self, config_file: str | Path) -> None:
        self.config_path = Path(config_file)

    def load_config(self) -> GameConfig:
        """Load config from path while tolerating invalid values and comments."""
        if not self.config_path.exists() or self.config_path.suffix.lower() != ".json":
            Parser._print_config_error(f"{self.config_path} "
                                       "is not a valid config file. "
                                       "Using the default configuration instead.")
            return GameConfig()

        try:
            content = self.config_path.read_text(encoding="utf-8")
            parsed = json.loads(self._strip_json_comments(content))
        except (OSError, json.JSONDecodeError):
            Parser._print_config_error(f"{self.config_path} "
                                       "is not a valid config file. "
                                       "Using the default configuration instead.")
            return GameConfig()

        if not isinstance(parsed, dict):
            Parser._print_config_error(f"{self.config_path} "
                                       "is not a valid config file. "
                                       "Using the default configuration instead.")
            return GameConfig()

        merged: dict[str, Any] = {
            "highscore_filename": _DEFAULT_CONFIG.highscore_filename,
            "levels": _DEFAULT_CONFIG.levels,
            "lives": _DEFAULT_CONFIG.lives,
            "points_per_pacgum": _DEFAULT_CONFIG.points_per_pacgum,
            "points_per_super_pacgum": _DEFAULT_CONFIG.points_per_super_pacgum,
            "points_per_ghost": _DEFAULT_CONFIG.points_per_ghost,
            "ghost_respawn_delay_seconds": (
                _DEFAULT_CONFIG.ghost_respawn_delay_seconds
            ),
            "seed": _DEFAULT_CONFIG.seed,
            "level_max_time": _DEFAULT_CONFIG.level_max_time,
        }

        all_keys = list(_INT_FIELDS) + ["highscore_filename", "levels"]
        for key in all_keys:
            if key not in parsed.keys():
                self._print_config_error(f"{key} not defined in {self.config_path}. "
                                         "Using the default value instead.")

        for key, value in parsed.items():
            key = key.lower()
            if key in _INT_FIELDS:
                merged[key] = self._coerce_non_negative_int(key, value, merged[key])
            elif key == "highscore_filename":
                merged[key] = self._coerce_non_empty_str(value, merged[key])
            elif key == "levels":
                merged[key] = self._coerce_levels(value, merged[key])

        try:
            return GameConfig(**merged)
        except ValidationError as e:
            print(e, file=sys.stderr)
            print("Using default configuration instead.", file=sys.stderr)
            return GameConfig()

    @staticmethod
    def _strip_json_comments(content: str) -> str:
        """Return JSON-compatible content by skipping full-line comments."""
        kept_lines: list[str] = []
        for line in content.splitlines():
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("//"):
                continue
            kept_lines.append(line)
        return "\n".join(kept_lines)

    @staticmethod
    def _coerce_non_negative_int(key: str, value: Any, default: int) -> int:
        """Convert value into a non-negative integer fallbacking to default."""
        if isinstance(value, bool):
            Parser._print_config_error(f"Value of {key} is not an integer. "
                                       "Using default value instead.")
            return default

        try:
            v = int(value)
        except (TypeError, ValueError):
            Parser._print_config_error(f"Value of {key} is not an integer. "
                                       "Using default value instead.")
            return default

        if key == "lives" or key == "levels":
            if v < 1:
                Parser._print_config_error(f"Value of {key} is too small. "
                                           "Using default value instead.")
                return default
        else:
            if v < 0:
                Parser._print_config_error(f"Value of {key} is not a positive integer. "
                                           "Using default value instead.")
                return default
        return v

    @staticmethod
    def _coerce_non_empty_str(value: Any, default: str) -> str:
        """Convert value into a non-empty stripped string fallbacking to default."""
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned and cleaned.endswith(".json"):
                return cleaned
        Parser._print_config_error("Highscore file is not a valid JSON filename. "
                                   "Using the default file 'highscore.json' instead.")
        return default

    @staticmethod
    def _coerce_levels(value: Any, default: list[tuple[int, int]]) \
            -> list[tuple[int, int]]:
        """Convert value into a list of tuple of integers."""
        if not isinstance(value, list):
            Parser._print_config_error("Levels are not correctly defined. "
                                       "Using the default value instead.")
            return default

        default_level = (_DEFAULT_LEVEL_WIDTH, _DEFAULT_LEVEL_HEIGHT)
        res: list[tuple[int, int]] = []
        for i, level in enumerate(value):
            if not isinstance(level, dict):
                Parser._print_config_error(f"Level {i + 1} is not correctly defined. "
                                           "Using the default value instead.")
                res.append(default_level)
                continue
            x = Parser._coerce_non_negative_int("levels", level.get("width"),
                                                _DEFAULT_LEVEL_WIDTH)
            y = Parser._coerce_non_negative_int("levels", level.get("height"),
                                                _DEFAULT_LEVEL_HEIGHT)
            res.append((x, y))

        length = len(res)
        if length < _MIN_LEVELS:
            Parser._print_config_error(f"There must be at least {_MIN_LEVELS} levels. "
                                       "Adding default levels until "
                                       f"there are {_MIN_LEVELS} levels.")
            missing = _MIN_LEVELS - length
            for i in range(missing):
                res.append(default_level)
        return res

    @staticmethod
    def _print_config_error(error: str) -> None:
        """Print an error message for an error when parsing the configuration file."""
        print("ConfigError: ", error, file=sys.stderr)
