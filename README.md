*This project has been created as part of the 42 curriculum by jhoban, yanlu.*

# Pac-Man

## Description
This repository contains a UV-managed Python skeleton for the 42 Pac-Man project.
It sets up package structure, configuration loading, highscore persistence, CLI entrypoint,
and the required quality tooling (flake8 + mypy) to support iterative game implementation.

## Project Management
Project management evidence is stored in `project_management/`
Link to Trello board: https://trello.com/b/ltiY3yB4/pac-man-42-project

## Instructions
### Requirements
- Python 3.10+
- [uv](https://docs.astral.sh/uv/)

### Setup
```bash
make install
```

### Run
```bash
make run
```

### Debug
```bash
make debug
```

### Lint / Type-check
```bash
make lint
# optional strict mode
make lint-strict
```

### Clean caches
```bash
make clean
```

## Configuration
The program expects one argument:
```bash
python3 pac-man.py config.json
```

The loader accepts `.json` files and ignores full-line comments beginning with `#` or `//`.
Unknown keys are ignored, and invalid values fall back to safe defaults.

Default keys:
- `highscore_filename`: `"highscores.json"`
- `levels`:
    - `width`: `21`
    - `height`: `21`
- `lives`: `3`
- `pacgum`: `42`
- `points_per_pacgum`: `10`
- `points_per_super_pacgum`: `50`
- `points_per_ghost`: `200`
- `seed`: `42`
- `level_max_time`: `90`

A template file is provided at `config.example.json`.

## Highscore
Highscores are stored in JSON (`highscores.json` by default).
The skeleton validates entries to keep names alphanumeric (plus spaces), max 10 chars,
forces non-negative integer scores, sorts by score, and keeps only the top 10 entries.

## Maze Generation
This skeleton reserves integration points for the assigned A-Maze-ing package.
The final implementation should add a dedicated adapter module that calls the external
maze generator with `PERFECT=False`, while keeping robust error handling in the game loop.

## Implementation
Implemented foundation modules:
- `pacman.app`: CLI argument handling and startup flow.
- `pacman.config`: resilient configuration loading with defaults.
- `pacman.highscore`: persistent highscore load/save helpers.
- `pac-man.py`: required launcher entrypoint.

## General Software Architecture
The project follows a modular package layout (`src/pacman`) with separation between:
- startup orchestration (`app`),
- I/O and parsing concerns (`config`),
- persistence logic (`highscore`).

This structure is intended to extend cleanly with future gameplay modules
(renderer, entities, ghost AI, menus, level manager, and maze adapter).

## Project Management
Project-management evidence should be stored in:
- `project_management/`

See `project_management/README.md` for scope.

## Resources
- 42 project subject (Pacman: Ghosts! More ghosts!)
- Python docs: https://docs.python.org/3/
- UV docs: https://docs.astral.sh/uv/
- flake8 docs: https://flake8.pycqa.org/
- mypy docs: https://mypy.readthedocs.io/
- Python arcade library docs: https://api.arcade.academy/en/stable/index.html

AI usage in this repository:
- Used AI to scaffold repetitive project setup tasks (UV packaging, Makefile baseline,
  README structure, and starter validation tests).
- All generated content was reviewed, edited, and validated before being kept.
