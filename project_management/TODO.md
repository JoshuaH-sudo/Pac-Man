# Pac-Man Project Todo List

This checklist is organized to match the subject requirements and the current repository state.

## 1. Foundation and Tooling
- [ ] Confirm `make install`, `make run`, `make debug`, `make lint`, and `make test` work from a clean environment.
- [ ] Add the graphical library dependency and document the install/run workflow.
- [ ] Decide the window size, tile size, frame timing, and input mapping.
- [ ] Define the core package layout for gameplay modules (`maze`, `game_state`, `entities`, `ui`, `renderer`, `input`).
- [ ] Keep all new modules `flake8` and `mypy` clean.

## 2. Configuration and Startup (yanlu -- 04.06.-05.06.)
- [x] Keep CLI behavior exactly `python3 pac-man.py config.json`.
- [x] Harden config parsing for missing files, invalid JSON, bad values, and unknown keys.
- [x] Support JSON comments beginning with `#` and `//`.
- [x] Clamp invalid values to safe defaults and print clear messages without tracebacks.
- [ ] Extend config structure if needed for graphics, controls, level count, timers, and cheat mode.
- [x] Update tests for all config edge cases.

## 3. Maze Generator Integration
- [ ] Inspect the assigned `mazegenerator-00001-py3-none-any.whl` interface.
- [ ] Build an adapter module around the assigned package without modifying it.
- [ ] Ensure maze generation uses `PERFECT=False`.
- [ ] Handle maze-generation failures gracefully with a user-facing error path.
- [ ] Convert generated maze data into game tiles, spawn points, corridors, and walls.
- [ ] Add tests for adapter behavior where feasible.

## 4. Core Game Loop and State Machine (yanlu 05.06 - )
- [x] Implement a main state machine for menu, gameplay, pause, game over, victory, and highscore entry.
- [x] Make the flow follow: Main Menu -> Start Game -> Win/Lose -> Enter Name -> Back to Main Menu.
- [x] Keep score, lives, level number, and time remaining in a central game session model.
- [ ] Preserve score and remaining lives across levels.
- [ ] Return cleanly to the main menu after a finished run.

## 5. Player Mechanics
- [ ] Spawn the player at the maze center.
- [ ] Support movement in 4 directions with arrow keys and/or WASD.
- [ ] Prevent movement through walls.
- [ ] Deduct a life on ghost collision when ghosts are not edible.
- [ ] Respawn the player correctly after losing a life.
- [ ] End the game when lives reach zero.

## 6. Pacgums, Super-Pacgums, and Scoring
- [ ] Populate most corridors with pacgums.
- [ ] Place 4 super-pacgums in maze corners.
- [ ] Add score for normal pacgums.
- [ ] Add score for super-pacgums.
- [ ] Add score for edible ghosts.
- [ ] Ensure score never decreases.
- [ ] Complete the level when all required pacgums are eaten.

## 7. Ghost Behavior
- [ ] Spawn 4 ghosts, one in each corner.
- [ ] Implement autonomous ghost movement through corridors.
- [ ] Define a simple but explainable chase behavior.
- [ ] Make ghosts enter an edible state after super-pacgum pickup.
- [ ] Make edible ghosts flee or behave differently from chase mode.
- [ ] Respawn eaten ghosts after a delay at their home corner.

## 8. Level Progression (yanlu 24.06 - )
- [ ] Support at least 10 levels.
- [x] Use a fixed seed for level 1.
- [ ] Use random generation for later levels.
- [ ] Add a per-level time limit.
- [x] Decide and implement timeout behavior.
- [x] Move to the next level on completion.
- [ ] End the game with victory after the final level.

## 9. User Interface (yanlu)
- [x] Build a main menu with Start Game, View Highscores, Instructions, and Exit. (05.06.-07.06.)
- [x] Build an always-visible HUD with score, lives, level, and remaining time. (23.06 - 24.06.)
- [x] Build a pause menu with Resume and Return to Main Menu. (18.06.)
- [x] Build a game-over screen with final score anccd highscore name entry. (16.06.)
- [x] Build a victory screen with final score, message, and highscore name entry. (16.06)
- [ ] Keep controls readable and evaluator-friendly.

## 10. Highscore System (yanlu 05.06.-17.06.)
- [x] Load highscores at game start.
- [x] Save highscores at game end.
- [x] Handle missing or malformed highscore files without crashing.
- [x] Validate player names: max 10 chars, alphanumeric and spaces only.
- [x] Validate scores as non-negative integers.
- [x] Keep only the top 10 sorted entries.
- [x] Display highscores from the main menu.

## 11. Cheat Mode for Evaluation
- [ ] Add a clear way to activate cheat mode.
- [ ] Implement invincibility.
- [ ] Implement level skip.
- [ ] Implement ghost freeze.
- [ ] Implement extra lives.
- [ ] Optionally implement increased player speed or another reviewer-friendly helper.
- [ ] Document cheat controls for peer review.

## 12. Testing and Validation
- [ ] Expand unit tests for config and highscore modules.
- [ ] Add tests for state transitions and critical game rules where possible.
- [ ] Add regression tests for validation edge cases.
- [ ] Run `make lint` regularly.
- [ ] Run `make test` regularly.
- [ ] Run `make lint-strict` before final submission if feasible.

## 13. Documentation and Project Evidence
- [ ] Keep `README.md` updated as implementation details change.
- [ ] Document the chosen graphical library and controls.
- [ ] Document maze integration once the adapter is implemented.
- [ ] Document the highscore design and storage choice.
- [ ] Add a technical implementation summary when gameplay modules exist.
- [ ] Create project-management evidence files in `project_management/`.
- [ ] Add planning, progress tracking, risk analysis, team organization, and acceptance-test evidence.

## 14. Packaging and Demo Readiness
- [ ] Choose a packaging approach suitable for public demo distribution.
- [ ] Add the packaging script or spec at repository root.
- [ ] Ensure the packaged build includes minimum controls/instructions.
- [ ] Verify the game can be regenerated for peer review.
- [ ] Prepare an unlisted/private upload target such as Itch.io.

## 15. Evaluation Readiness
- [ ] Review every feature against the subject PDF.
- [ ] Rehearse explaining the maze adapter, game loop, ghost logic, and highscore flow.
- [ ] Be ready to make a small live code change during defense.
- [ ] Verify there are no normal user flows that trigger a traceback.
- [ ] Do one final full run-through from menu to win/lose to highscore save.
