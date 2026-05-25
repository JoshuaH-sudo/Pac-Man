"""Pac-Man application entrypoint."""

from __future__ import annotations

from pathlib import Path
import sys

from pacman.config import load_config
from pacman.highscore import load_highscores


USAGE = "Usage: python3 pac-man.py config.json"


def _print_error(message: str) -> None:
    """Print a user-friendly error message."""
    print(f"Error: {message}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    """Run the Pac-Man skeleton app."""
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        _print_error("exactly one .json configuration file is required")
        print(USAGE, file=sys.stderr)
        return 1

    config_path = Path(args[0])
    if config_path.suffix.lower() != ".json":
        _print_error("configuration file must use the .json extension")
        print(USAGE, file=sys.stderr)
        return 1

    config = load_config(config_path)
    highscores = load_highscores(config.highscore_filename)

    print("Pac-Man skeleton initialized.")
    print(f"Config source: {config_path}")
    print(f"Configured lives: {config.lives}")
    print(f"Loaded highscores: {len(highscores)}")
    return 0
