#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT_DIR"

echo "Installing/updating dependencies..."
UV_SKIP_WHEEL_FILENAME_CHECK=1 uv sync --all-groups

echo "Building distributable package with PyInstaller..."
UV_SKIP_WHEEL_FILENAME_CHECK=1 uv run pyinstaller --noconfirm --clean pacman.spec

echo "Build complete."
echo "Output folder: dist/pac-man"
echo "Archive this folder for upload to private/unlisted Itch.io or Steam builds."
