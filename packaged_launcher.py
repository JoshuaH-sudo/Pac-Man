"""Launcher used for distributable builds (Steam/Itch.io private uploads)."""

from __future__ import annotations

import json
from pathlib import Path
import os
import sys
from typing import Any

from pacman.app import main


def _bundle_dir() -> Path:
    """Return the directory that contains packaged runtime resources."""
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if isinstance(meipass, str):
            return Path(meipass)
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _user_data_dir() -> Path:
    """Return a writable directory for highscores and runtime config."""
    app_name = "PacMan42"
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif os.name == "nt":
        base = Path(os.getenv("APPDATA", str(Path.home())))
    else:
        base = Path(os.getenv("XDG_DATA_HOME", str(Path.home() / ".local" / "share")))

    target = base / app_name
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise RuntimeError(
            f"Unable to create user data directory at '{target}'."
        ) from exc
    return target


def _load_packaged_config(config_path: Path) -> dict[str, Any]:
    """Load bundled JSON config while tolerating malformed files."""
    try:
        loaded = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    if isinstance(loaded, dict):
        return loaded
    return {}


def _write_runtime_config() -> Path:
    """Generate a writable config file path and return it."""
    bundle_dir = _bundle_dir()
    data_dir = _user_data_dir()

    external_config = Path(sys.executable).resolve().parent / "config.json"
    bundled_config = bundle_dir / "config.example.json"

    config_source = external_config if external_config.exists() else bundled_config
    config_data = _load_packaged_config(config_source)

    config_data["highscore_filename"] = str(data_dir / "highscores.json")

    runtime_config = data_dir / "runtime-config.json"
    try:
        runtime_config.write_text(json.dumps(config_data, indent=2), encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(
            f"Unable to write runtime config to '{runtime_config}'."
        ) from exc
    return runtime_config


def run() -> int:
    """Start the packaged game using a generated runtime config."""
    runtime_config = _write_runtime_config()
    return main([str(runtime_config)])


if __name__ == "__main__":
    raise SystemExit(run())
