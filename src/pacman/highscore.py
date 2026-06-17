"""Persistent highscore helpers for Pac-Man."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any

_NAME_PATTERN = re.compile(r"^[A-Za-z0-9 ]+$")


@dataclass(slots=True)
class HighscoreEntry:
    """A single highscore entry."""

    name: str
    score: int


class HighScore:
    def __init__(self, file: str | Path) -> None:
        self.path = file

    @staticmethod
    def sanitize_name(raw_name: str) -> str:
        """Normalize a player name to the project constraints."""
        name = raw_name.strip()[:10]
        if not name or not _NAME_PATTERN.fullmatch(name):
            print("Invalid player name. Using default instead.\n"
                  "Player name can only consist of alphanumeric characters"
                  " and spaces.",
                  file=sys.stderr)
            return "PLAYER"
        return name

    @staticmethod
    def sanitize_score(raw_score: Any) -> int:
        """Normalize score values to non-negative integers."""
        if isinstance(raw_score, bool):
            return 0
        if isinstance(raw_score, int):
            return max(0, raw_score)
        return 0

    @staticmethod
    def _to_entry(item: Any) -> HighscoreEntry | None:
        """Build a validated highscore entry from untyped data."""
        if not isinstance(item, dict):
            return None
        raw_name = item.get("name")
        raw_score = item.get("score")
        if not isinstance(raw_name, str):
            return None
        return HighscoreEntry(name=HighScore.sanitize_name(raw_name),
                              score=HighScore.sanitize_score(raw_score))

    def load_highscores(self) -> list[HighscoreEntry]:
        """Load highscores from disk while tolerating format errors."""
        score_path = Path(self.path)
        if not score_path.exists():
            print("No highscores yet.", file=sys.stderr)
            return []

        try:
            loaded = json.loads(score_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            print(f"No highscores can be loaded from file: {self.path}.",
                  file=sys.stderr)
            return []

        if not isinstance(loaded, list):
            print(f"No highscores can be loaded highscores from file: {self.path}.",
                  file=sys.stderr)
            return []

        entries = [entry for item in loaded
                   if (entry := HighScore._to_entry(item)) is not None]
        entries.sort(key=lambda entry: entry.score, reverse=True)
        return entries[:10]

    def save_highscores(self, scores: list[HighscoreEntry]) -> None:
        """Persist highscores in JSON format."""
        score_path = Path(self.path)
        top_scores = sorted(scores, key=lambda entry: entry.score, reverse=True)[:10]
        payload = [asdict(entry) for entry in top_scores]
        score_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
