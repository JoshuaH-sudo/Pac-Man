# Multi-Level Progression Implementation

## Overview
The Pac-Man game now supports multiple levels with dynamic maze generation. Each level has its own maze dimensions specified in `config.json`, and players must complete all levels to win the game.

## How It Works

### Level Configuration
Levels are defined in `config.json` with their respective maze dimensions:

```json
{
  "levels": [
    { "width": 10, "height": 10 },
    { "width": 21, "height": 21 },
    { "width": 22, "height": 22 },
    // ... up to 10 levels minimum
  ]
}
```

### Level Progression
1. **Complete a Level**: Eat all pacgums (regular and super) without losing all lives and before the timer expires
2. **Advance to Next Level**: A new maze is automatically generated with the dimensions for the next level
3. **Reset State**: Each level:
   - Regenerates the maze from scratch
   - Resets pacgum counts and item lists
   - Resets ghost vulnerability status
   - Maintains score and lives across levels
4. **Win Condition**: Complete all levels defined in `config.json`
5. **Lose Condition**: Lose all lives OR run out of time on any level

## Technical Implementation

### Key Changes in `src/pacman/game/game_view.py`

#### New Method: `_load_level()`
Generates and initializes a new maze for the current level:
- Extracts maze dimensions from `config.levels[current_level - 1]`
- Creates a new maze using `MazeGenerator`
- Builds item cells (regular pacgums and super pacgums)
- Builds ghost spawn cells in maze corners
- Resets ghost vulnerability
- Reinitializes movement controller

```python
def _load_level(self) -> None:
    """Generate and initialize a new maze for the current level."""
    # Gets dimensions from config
    level_width, level_height = self.config.levels[self.state.level - 1]
    
    # Generate maze
    generator = MazeGenerator(
        size=(level_width, level_height),
        perfect=False,
        seed=self.config.seed if self.state.level == 1 else 0,
    )
    # ... rest of level initialization
```

#### Modified: `on_update()`
Now handles level advancement and maze regeneration:
- Checks when all pacgums are eaten
- Advances to the next level
- Calls `_load_level()` to generate the new maze
- Syncs entities to the new maze
- Checks for win condition (completed all levels)
- Checks for lose conditions (no lives or timeout)

```python
# Check if level is completed
if self.state.lives > 0 and self.state.timer >= 0 \
        and all_gums_eaten >= self._count_pacgums:
    self.state.advance_level()
    
    # Load the next level if not at the end
    if self.state.level <= len(self.config.levels):
        self._load_level()
        self._sync_entities_to_maze()
```

#### Modified: `on_show_view()`
Now loads the first level when the game view is displayed:
```python
def on_show_view(self) -> None:
    arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
    if not self._level_loaded:
        self._load_level()
    if not self._initialized:
        self._sync_entities_to_maze()
        self._initialized = True
    self.manager.enable()
```

#### Null Safety
Added proper None-checks for `_maze_display` throughout the code to ensure type safety:
- `on_draw()`: Checks before drawing maze
- `on_update()`: Checks before updating movement
- `_update_ghosts()`: Checks before updating ghost AI
- `_sync_entities_to_maze()`: Checks before syncing positions
- `_rebuild_wall_colliders()`: Checks before building walls
- `_cell_indices_for_position()`: Checks before calculating cell indices
- `_clamp_cell_indices()`: Safe fallback for clamping

## Game Flow

```
Main Menu
    ↓
Game Start (Level 1)
    ↓
Generate Maze (Level 1 dimensions from config)
    ↓
Play Level
    ├─→ Win Level: All pacgums eaten, time remaining, lives > 0
    │       ↓
    │   Check: More levels?
    │       ├─→ YES: Load Next Level (repeat)
    │       └─→ NO: Victory Screen
    │
    └─→ Lose Level: Out of lives OR timeout
            ↓
        Game Over Screen
```

## Configuration Tips

- **Minimum levels**: 10 (enforced by config validation)
- **Level difficulty**: Typically, increase maze size for harder levels
- **Seed handling**: Level 1 uses the configured seed for reproducibility; subsequent levels use seed 0 for variation
- **Timer**: Same for all levels (configured via `level_max_time`)

## Testing the Feature

1. Start the game: `python3 pac-man.py config.json`
2. Complete a level (eat all pacgums)
3. The next level's maze should automatically generate
4. Progress through all 10 levels to win

## Example Config for Testing

```json
{
  "highscore_filename": "highscores.json",
  "lives": 3,
  "points_per_pacgum": 10,
  "points_per_super_pacgum": 50,
  "points_per_ghost": 200,
  "seed": 42,
  "level_max_time": 120,
  "levels": [
    { "width": 10, "height": 10 },
    { "width": 15, "height": 15 },
    { "width": 19, "height": 19 },
    { "width": 21, "height": 21 },
    { "width": 23, "height": 23 },
    { "width": 25, "height": 25 },
    { "width": 27, "height": 27 },
    { "width": 29, "height": 29 },
    { "width": 31, "height": 31 },
    { "width": 33, "height": 33 }
  ]
}
```
