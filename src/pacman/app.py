"""Pac-Man application entrypoint."""

from __future__ import annotations

from pathlib import Path
import sys

import arcade

from pacman.config import load_config
from pacman.highscore import load_highscores
from mazegenerator import MazeGenerator

from pacman.window import create_game_window


USAGE = "Usage: python3 pac-man.py config.json"
MAZE_SIZE = (21, 21)


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

    # Use an odd-sized maze so the layout has a true center cell.
    maze_gen = MazeGenerator(size=MAZE_SIZE)

    # Get the maze structure
    maze_grid = maze_gen.maze
    shortest_path = maze_gen.shortest_path

    print(f"Maze dimensions: {len(maze_grid[0])}x{len(maze_grid)}")
    print(f"Entry: {maze_gen.maze_entry}, Exit: {maze_gen.maze_exit}")
    for row in maze_grid:
        # print hexadecimal values for better visualization
        print("".join(f"{cell:2X}" for cell in row))
    print(f"Shortest path length: {shortest_path}")

    create_game_window(maze_grid)

    # Start the arcade game loop
    arcade.run()

    return 0
