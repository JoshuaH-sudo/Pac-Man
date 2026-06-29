*This project has been created as part of the 42 curriculum by jhoban, yanlu.*

# Pac-Man

## Description
This project recreates a complete and playable Pac-Man game in Python, using
object-oriented programming, the graphical library `arcade`, and a modular, reusable architecture.

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
    - `width`: `14`
    - `height`: `14`
- `lives`: `3`
- `points_per_pacgum`: `10`
- `points_per_super_pacgum`: `50`
- `points_per_ghost`: `200`
- `ghost_respawn_delay_seconds`: `5`
- `seed`: `42`
- `level_max_time`: `90`

A template file is provided at `config.example.json`.

## In game controls
Press the arrow keys or WASD to move the player.

Eating pacgums will increase your score.

Touching a ghost will make you lose one life.

Eating a super-pacgum will make the ghost edible for a short period.

Ghosts will respawn after a while after being eaten.

To complete a level, eat all pacgums in the level within the time limit and without losing all lives.

To win the game, complete all levels.

Game over if you fail to complete a level within the time limit or lost all lives

## Cheat mode
Press the `C` key in game to activate cheat mode and press again to deactivate it.

In cheat mode, player will have infinite lives and infinite time, and can:
- Press `N` to immediately advance to the next level.
- Press `O` to immediately lose the game.
- Press `V` to immediately win the game.

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
The project progress is managed using Trello board: https://trello.com/b/ltiY3yB4/pac-man-42-project

Additional project-management evidence is stored in `project_management/`

## Resources
- Python docs: https://docs.python.org/3/
- UV docs: https://docs.astral.sh/uv/
- flake8 docs: https://flake8.pycqa.org/
- mypy docs: https://mypy.readthedocs.io/
- Python arcade library docs: https://api.arcade.academy/en/stable/index.html

AI usage in this repository:
- Used AI to scaffold repetitive project setup tasks (UV packaging, Makefile baseline,
  README structure, and starter validation tests).
- All generated content was reviewed, edited, and validated before being kept.
