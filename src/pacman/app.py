"""Pac-Man application entrypoint."""

from __future__ import annotations

from pathlib import Path
import sys

import arcade

from pacman.core import Parser, CLOSED_EAST, CLOSED_NORTH, CLOSED_SOUTH, CLOSED_WEST
from pacman.core import WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH
from pacman.game import GameView
from pacman.ui.main_menu import MainMenu

USAGE = "Usage: python3 pac-man.py config.json"
MAZE_SIZE = (10, 10)


def _print_error(message: str) -> None:
    """Print a user-friendly error message."""
    print(f"Error: {message}", file=sys.stderr)


def _build_test_loop_maze() -> list[list[int]]:
    """Build a 2x10 rectangular loop with a shared middle wall segment."""
    rows = 2
    cols = 10
    maze: list[list[int]] = []

    for row in range(rows):
        row_values: list[int] = []
        for col in range(cols):
            cell_value = 0
            if row == 0:
                cell_value |= CLOSED_NORTH
            if row == rows - 1:
                cell_value |= CLOSED_SOUTH
            if col == 0:
                cell_value |= CLOSED_WEST
            if col == cols - 1:
                cell_value |= CLOSED_EAST

            # Add the middle shared wall except on both ends, so the two rows
            # connect only at left and right edges and form one loop.
            if row == 0 and 0 < col < cols - 1:
                cell_value |= CLOSED_SOUTH
            if row == 1 and 0 < col < cols - 1:
                cell_value |= CLOSED_NORTH

            row_values.append(cell_value)
        maze.append(row_values)

    return maze


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

    config = Parser(config_path).load_config()
    print(config)

    print("Pac-Man skeleton initialized.")
    print(f"Config source: {config_path}")
    print(f"Configured lives: {config.lives}")
    # print(f"Loaded highscores: {len(highscores)}")

    # Deterministic test maze: 2x10 rectangle with a shared middle wall and
    # openings at both ends, creating a single loop track.
    maze_grid = _build_test_loop_maze()

    print(f"Maze dimensions: {len(maze_grid[0])}x{len(maze_grid)}")
    for row in maze_grid:
        # print hexadecimal values for better visualization
        print("".join(f"{cell:2X}" for cell in row))

    # Create a window class. This is what actually shows up on screen
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)

    # Create and setup the GameView
    game = GameView(maze_grid)
    menu = MainMenu(game, config)
    menu.instruction.main_menu = menu

    # Show GameView on screen
    window.show_view(menu)

    # Start the arcade game loop
    arcade.run()

    return 0
