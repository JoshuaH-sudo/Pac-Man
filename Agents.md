# AGENTS.md

## Purpose
This file defines how coding agents should work in this repository so the project stays aligned with `en.subject.pdf` (Pacman: Ghosts! More ghosts!, v1.4).

## Source of Truth
1. `en.subject.pdf`
2. `README.md`
3. `Makefile`
4. Existing tests in `tests/`

If there is a conflict, follow that order.

## Non-Negotiable Standards
- Python version: 3.10+
- Style: `flake8` clean
- Typing: `mypy` clean for all functions
- Exceptions: no unhandled traceback in normal error scenarios
- Resource handling: use context managers where applicable
- Documentation: PEP 257 docstrings for functions/classes
- CLI contract: exactly one argument (`config.json` path)

## Required Commands Before Merging
Run all commands from repository root:

```bash
make lint
make test
```

Recommended in addition:

```bash
make lint-strict
```

## Delivery Scope Checklist (Subject-Aligned)
Agents should treat each item as a done criterion.

### Core runtime
- [ ] Program runs as: `python3 pac-man.py config.json`
- [ ] Missing/invalid config is handled with clear messages (no traceback)
- [ ] Unknown config keys are ignored
- [ ] Invalid/missing values are clamped/fallback to safe defaults
- [ ] JSON comments are supported (`#`, and `//` if implemented)

### Maze integration
- [ ] Uses assigned A-Maze-ing package as-is (no modification)
- [ ] Adapter matches package interface
- [ ] Passes `PERFECT=False`
- [ ] Generator failures are handled gracefully

### Highscore
- [ ] Persistent highscore storage
- [ ] Robust to file not found / malformed file
- [ ] Name validation: max 10 chars, alphanumeric + spaces
- [ ] Score validation: non-negative integers
- [ ] Keeps top 10 sorted entries
- [ ] Loads at game start, saves at game end
- [ ] Name input flow appears on win and lose screens

### Game features
- [ ] Multiple levels (minimum 10)
- [ ] Level timer handling
- [ ] Pacgum/super-pacgum scoring rules
- [ ] 4 ghosts + edible state behavior
- [ ] Pause/resume flow
- [ ] Cheat mode that helps peer evaluation

### UI flow
- [ ] Main menu (Start, Highscores, Instructions, Exit)
- [ ] In-game HUD (score, lives, level, remaining time)
- [ ] Pause menu (Resume, Main Menu)
- [ ] Game-over and victory screens with highscore prompt
- [ ] Game loop returns to main menu after end state

### Project artifacts
- [ ] Root `README.md` satisfies required sections from subject
- [ ] `project_management/` exists with evidence artifacts
- [ ] Packaging script/spec is at repository root
- [ ] Build can be prepared for platform distribution

## Agent Working Rules
- Make small, focused commits/changes.
- Never replace external maze package code.
- Preserve public interfaces unless a requirement demands change.
- Add or update tests when behavior changes.
- Update `README.md` when config, gameplay, architecture, or persistence changes.
- Prefer explicit validation and deterministic behavior for evaluator scenarios.

## Suggested Implementation Order
1. Configuration parser and error handling hardening
2. Maze adapter integration (`PERFECT=False`)
3. Core loop state machine (menu, game, pause, game over, victory)
4. Entity rules (player, ghosts, pacgums, super-pacgums)
5. Scoring and highscore persistence
6. Cheat mode and evaluator shortcuts
7. Tests for parser/highscore and critical game-state transitions
8. Project-management and packaging evidence

## Installed Skills (Global)
Installed with `npx skills add ... -g -y`:
- `wshobson/agents@python-testing-patterns`
- `affaan-m/everything-claude-code@python-testing`
- `sickn33/antigravity-awesome-skills@game-development`

## Skill Usage Guidance
- Use `python-testing-patterns` for robust unit/integration test design.
- Use `python-testing` for fixture strategy and edge-case coverage.
- Use `game-development` for gameplay-loop and systems design patterns.

All generated code must still be reviewed, understood, and adjusted to fit this subject and this codebase.