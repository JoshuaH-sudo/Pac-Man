"""Arcade window and maze rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import arcade
from arcade.types import Color

from pacman.entities import Pacgum, Pacman

WINDOW_WIDTH = 1024
WINDOW_HEIGHT = 768
WINDOW_TITLE = "Pac-Man"

CLOSED_NORTH = 0b0001
CLOSED_EAST = 0b0010
CLOSED_SOUTH = 0b0100
CLOSED_WEST = 0b1000

PLAYER_MOVEMENT_SPEED = 10
PLAYER_CELL_FRACTION = 0.9
ITEM_CELL_FRACTION = 0.45
PACGUM_ANIMATION_FPS = 8.0
MAZE_MARGIN = 12.0
PLAYER_SPEED_RATIO = 0.09
MAX_COLLISION_WALL_THICKNESS = 4.0
COLLISION_WALL_THICKNESS_RATIO = 0.08

GridPoint = tuple[int, int]
WallSegment = tuple[GridPoint, GridPoint]
WallCollider = tuple[float, float, float, float]
Direction = tuple[int, int]


@dataclass(frozen=True)
class MazePointGrid:
    """Point-grid representation derived from integer maze cells."""

    rows: int
    cols: int
    points: tuple[GridPoint, ...]
    wall_segments: tuple[WallSegment, ...]

    @classmethod
    def from_maze_grid(
        cls,
        maze_grid: Sequence[Sequence[int]],
    ) -> "MazePointGrid":
        """Parse maze cell bitmasks into corner points and wall segments."""
        if not maze_grid or not maze_grid[0]:
            raise ValueError(
                "maze_grid must be a non-empty rectangular matrix"
            )

        rows = len(maze_grid)
        cols = len(maze_grid[0])
        if any(len(row) != cols for row in maze_grid):
            raise ValueError("maze_grid rows must have equal length")

        points = tuple(
            (x, y)
            for y in range(rows + 1)
            for x in range(cols + 1)
        )
        wall_segments: set[WallSegment] = set()

        for y, row in enumerate(maze_grid):
            for x, cell in enumerate(row):
                cell_value = int(cell)
                if cell_value & CLOSED_NORTH:
                    wall_segments.add(_normalize_segment((x, y), (x + 1, y)))
                if cell_value & CLOSED_EAST:
                    wall_segments.add(
                        _normalize_segment((x + 1, y), (x + 1, y + 1))
                    )
                if cell_value & CLOSED_SOUTH:
                    wall_segments.add(
                        _normalize_segment((x, y + 1), (x + 1, y + 1))
                    )
                if cell_value & CLOSED_WEST:
                    wall_segments.add(_normalize_segment((x, y), (x, y + 1)))

        return cls(
            rows=rows,
            cols=cols,
            points=points,
            wall_segments=tuple(sorted(wall_segments)),
        )


def _normalize_segment(start: GridPoint, end: GridPoint) -> WallSegment:
    """Keep segment ordering stable so duplicate walls collapse into one."""
    return (start, end) if start <= end else (end, start)


def _center_cell_index(cell_count: int) -> int:
    """Return the nearest discrete center cell index for a maze axis."""
    return max(0, (cell_count - 1) // 2)


def _choose_initial_direction(cell_value: int) -> Direction:
    """Pick the first open direction in reading order for a maze cell."""
    if _direction_is_open(cell_value, (0, 1)):
        return (0, 1)
    if _direction_is_open(cell_value, (1, 0)):
        return (1, 0)
    if _direction_is_open(cell_value, (-1, 0)):
        return (-1, 0)
    if _direction_is_open(cell_value, (0, -1)):
        return (0, -1)
    return (0, 0)


def _direction_is_open(cell_value: int, direction: Direction) -> bool:
    """Return whether a maze cell allows travel in the given direction."""
    if direction == (0, 1):
        return not bool(cell_value & CLOSED_NORTH)
    if direction == (1, 0):
        return not bool(cell_value & CLOSED_EAST)
    if direction == (0, -1):
        return not bool(cell_value & CLOSED_SOUTH)
    if direction == (-1, 0):
        return not bool(cell_value & CLOSED_WEST)
    return False


def _nearest_cell_center(
    coordinate: float,
    offset: float,
    cell_size: float,
) -> float:
    """Return the nearest maze cell center coordinate for a screen axis."""
    cell_index = _nearest_cell_index(coordinate, offset, cell_size)
    return offset + (cell_index + 0.5) * cell_size


def _nearest_cell_index(
    coordinate: float,
    offset: float,
    cell_size: float,
) -> int:
    """Return the nearest maze cell index for a screen axis."""
    return int(round((coordinate - offset) / cell_size - 0.5))


def _resolve_player_direction(
    current_direction: Direction,
    desired_direction: Direction,
    center_x: float,
    center_y: float,
    cell_size: float,
    offset_x: float,
    offset_y: float,
) -> tuple[Direction, float, float]:
    """Keep travel axis-aligned and snap turns onto the cell grid."""
    alignment_tolerance = max(1.0, cell_size * 0.25)
    next_direction = current_direction or desired_direction
    snapped_x = center_x
    snapped_y = center_y

    if next_direction[0] != 0:
        lane_y = _nearest_cell_center(center_y, offset_y, cell_size)
        if abs(center_y - lane_y) <= alignment_tolerance:
            snapped_y = lane_y
            if desired_direction[1] != 0:
                turn_x = _nearest_cell_center(center_x, offset_x, cell_size)
                if abs(center_x - turn_x) <= alignment_tolerance:
                    snapped_x = turn_x
                    next_direction = desired_direction
            elif desired_direction[0] != 0:
                next_direction = desired_direction

    elif next_direction[1] != 0:
        lane_x = _nearest_cell_center(center_x, offset_x, cell_size)
        if abs(center_x - lane_x) <= alignment_tolerance:
            snapped_x = lane_x
            if desired_direction[0] != 0:
                turn_y = _nearest_cell_center(center_y, offset_y, cell_size)
                if abs(center_y - turn_y) <= alignment_tolerance:
                    snapped_y = turn_y
                    next_direction = desired_direction
            elif desired_direction[1] != 0:
                next_direction = desired_direction

    return next_direction, snapped_x, snapped_y


def _coerce_blocked_directions(
    current_direction: Direction,
    desired_direction: Direction,
    cell_value: int,
) -> tuple[Direction, Direction]:
    """Stop movement when blocked and keep only immediately valid directions."""
    next_current = current_direction
    next_desired = desired_direction

    if next_current != (0, 0) and not _direction_is_open(cell_value, next_current):
        next_current = (0, 0)
        next_desired = (0, 0)

    if next_current == (0, 0) and next_desired != (0, 0):
        if not _direction_is_open(cell_value, next_desired):
            next_desired = (0, 0)

    return next_current, next_desired


class MazeDisplay:
    """Render maze walls from a point-grid onto an Arcade view."""

    def __init__(
        self,
        maze_grid: Sequence[Sequence[int]],
        margin: float = MAZE_MARGIN,
        wall_color: Color = arcade.color.ALICE_BLUE,
        wall_width: float = 2.0,
    ) -> None:
        self._point_grid = MazePointGrid.from_maze_grid(maze_grid)
        self._margin = margin
        self._wall_color = wall_color
        self._wall_width = wall_width

    def draw(self, window_width: int, window_height: int) -> None:
        """Draw all closed walls scaled to the current window size."""
        cell_size, offset_x, offset_y = self.layout_for_window(
            window_width,
            window_height,
        )

        for (
            (start_x, start_y),
            (end_x, end_y),
        ) in self._point_grid.wall_segments:
            x1 = offset_x + start_x * cell_size
            y1 = window_height - (offset_y + start_y * cell_size)
            x2 = offset_x + end_x * cell_size
            y2 = window_height - (offset_y + end_y * cell_size)
            arcade.draw_line(
                x1,
                y1,
                x2,
                y2,
                self._wall_color,
                self._wall_width,
            )

    def wall_colliders(
        self,
        window_width: int,
        window_height: int,
    ) -> tuple[WallCollider, ...]:
        """Return wall-aligned collision boxes for the current window size."""
        cell_size, offset_x, offset_y = self.layout_for_window(
            window_width,
            window_height,
        )
        thickness = max(
            1.0,
            min(
                max(self._wall_width * 2.0, 1.0),
                cell_size * COLLISION_WALL_THICKNESS_RATIO,
                MAX_COLLISION_WALL_THICKNESS,
            ),
        )
        colliders: list[WallCollider] = []

        for (start_x, start_y), (end_x, end_y) in self._point_grid.wall_segments:
            if start_x == end_x:
                colliders.append(
                    (
                        offset_x + start_x * cell_size,
                        window_height
                        - (offset_y + ((start_y + end_y) * cell_size / 2.0)),
                        thickness,
                        abs(end_y - start_y) * cell_size + thickness,
                    )
                )
                continue

            colliders.append(
                (
                    offset_x + ((start_x + end_x) * cell_size / 2.0),
                    window_height - (offset_y + start_y * cell_size),
                    abs(end_x - start_x) * cell_size + thickness,
                    thickness,
                )
            )

        return tuple(colliders)

    @property
    def rows(self) -> int:
        """Maze row count in cells."""
        return self._point_grid.rows

    @property
    def cols(self) -> int:
        """Maze column count in cells."""
        return self._point_grid.cols

    def layout_for_window(
        self,
        window_width: int,
        window_height: int,
    ) -> tuple[float, float, float]:
        """Compute scale and offsets that center the maze in the viewport."""
        usable_w = max(1.0, window_width - (self._margin * 2.0))
        usable_h = max(1.0, window_height - (self._margin * 2.0))

        cell_size = min(
            usable_w / self._point_grid.cols,
            usable_h / self._point_grid.rows,
        )
        offset_x = (window_width - self._point_grid.cols * cell_size) / 2.0
        offset_y = (window_height - self._point_grid.rows * cell_size) / 2.0
        return cell_size, offset_x, offset_y

    def cell_center(
        self,
        window_width: int,
        window_height: int,
        cell_x: float,
        cell_y: float,
    ) -> tuple[float, float]:
        """Return on-screen center coordinates for a maze cell coordinate."""
        cell_size, offset_x, offset_y = self.layout_for_window(
            window_width,
            window_height,
        )
        center_x = offset_x + (cell_x + 0.5) * cell_size
        center_y = window_height - (offset_y + (cell_y + 0.5) * cell_size)
        return center_x, center_y


class GameView(arcade.View):
    """Main game view that currently renders the generated maze walls."""

    def __init__(self, maze_grid: Sequence[Sequence[int]]):
        super().__init__()
        self._maze_grid = tuple(tuple(int(cell) for cell in row) for row in maze_grid)
        self._maze_display = MazeDisplay(maze_grid)
        self._player_cell_x = _center_cell_index(self._maze_display.cols)
        self._player_cell_y = _center_cell_index(self._maze_display.rows)
        self._item_cell_x = min(
            self._maze_display.cols - 1,
            self._player_cell_x + 2,
        )
        self._item_cell_y = max(0, self._player_cell_y - 2)

        center_cell_value = int(
            maze_grid[self._player_cell_y][self._player_cell_x]
        )

        self._player = Pacman(
            center_x=0.0,
            center_y=0.0,
            speed=PLAYER_MOVEMENT_SPEED,
            scale=1.0,
        )
        self._players: arcade.SpriteList = arcade.SpriteList()
        self._players.append(self._player)
        self._walls: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        self._physics_engine: arcade.PhysicsEngineSimple | None = None

        self._items: arcade.SpriteList = arcade.SpriteList()
        self._items.append(
            Pacgum(
                center_x=0.0,
                center_y=0.0,
                scale=1.0,
                animation_fps=PACGUM_ANIMATION_FPS,
            )
        )

        self._current_direction = _choose_initial_direction(center_cell_value)
        self._desired_direction = self._current_direction
        self._queued_direction: Direction = (0, 0)
        self._lock_movement_for_spawn = True

    def on_show_view(self) -> None:
        arcade.set_background_color(arcade.color.DARK_BLUE_GRAY)
        self._sync_entities_to_maze()

    def on_resize(self, width: int, height: int) -> None:
        super().on_resize(width, height)
        self._sync_entities_to_maze()

    def on_draw(self) -> None:
        self.clear()
        self._maze_display.draw(self.window.width, self.window.height)
        self._items.draw()
        self._players.draw()

    def on_update(self, delta_time: float) -> None:
        if self._lock_movement_for_spawn:
            self._player.move(horizontal=0, vertical=0)
            self._lock_movement_for_spawn = False
        else:
            self._apply_player_movement()
        if self._physics_engine is None:
            self._players.update()
        else:
            self._physics_engine.update()
        self._keep_player_on_lane()
        self._players.update_animation(delta_time=delta_time)
        self._items.update_animation(delta_time=delta_time)
        self._keep_player_on_screen()

    def on_key_press(self, symbol: int, modifiers: int) -> None:
        del modifiers
        next_direction: Direction | None = None
        if symbol in (arcade.key.LEFT, arcade.key.A):
            next_direction = (-1, 0)
        if symbol in (arcade.key.RIGHT, arcade.key.D):
            next_direction = (1, 0)
        if symbol in (arcade.key.UP, arcade.key.W):
            next_direction = (0, 1)
        if symbol in (arcade.key.DOWN, arcade.key.S):
            next_direction = (0, -1)

        if next_direction is None:
            return

        self._queued_direction = next_direction

        if self.window is None:
            return

        cell_value = self._current_cell_value()
        if _direction_is_open(cell_value, self._queued_direction):
            self._desired_direction = self._queued_direction
            self._queued_direction = (0, 0)

    def on_key_release(self, symbol: int, modifiers: int) -> None:
        del modifiers
        del symbol

    def _apply_player_movement(self) -> None:
        if self.window is None:
            return

        cell_value = self._current_cell_value()

        if self._queued_direction != (0, 0):
            if _direction_is_open(cell_value, self._queued_direction):
                self._desired_direction = self._queued_direction
                self._queued_direction = (0, 0)

        self._current_direction, self._desired_direction = _coerce_blocked_directions(
            self._current_direction,
            self._desired_direction,
            cell_value,
        )

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        self._current_direction, self._player.center_x, self._player.center_y = (
            _resolve_player_direction(
                self._current_direction,
                self._desired_direction,
                self._player.center_x,
                self._player.center_y,
                cell_size,
                offset_x,
                offset_y,
            )
        )
        self._player.move(
            horizontal=self._current_direction[0],
            vertical=self._current_direction[1],
        )

    def _keep_player_on_screen(self) -> None:
        width = self.window.width
        height = self.window.height
        half_w = self._player.width / 2
        half_h = self._player.height / 2

        self._player.center_x = max(
            half_w,
            min(width - half_w, self._player.center_x),
        )
        self._player.center_y = max(
            half_h,
            min(height - half_h, self._player.center_y),
        )

    def _sync_entities_to_maze(self) -> None:
        if self.window is None:
            return

        self._player_cell_x = max(
            0,
            min(self._maze_display.cols - 1, int(round(self._player_cell_x))),
        )
        self._player_cell_y = max(
            0,
            min(self._maze_display.rows - 1, int(round(self._player_cell_y))),
        )

        cell_size, _, _ = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )

        self._player.scale = (
            (cell_size * PLAYER_CELL_FRACTION)
            / max(1.0, float(self._player.texture.width))
        )
        self._player.set_speed(cell_size * PLAYER_SPEED_RATIO)
        self._player.center_x, self._player.center_y = self._maze_display.cell_center(
            self.window.width,
            self.window.height,
            float(self._player_cell_x),
            float(self._player_cell_y),
        )
        self._rebuild_wall_colliders()
        center_cell_value = int(
            self._maze_grid[self._player_cell_y][self._player_cell_x]
        )
        self._current_direction = _choose_initial_direction(center_cell_value)
        self._desired_direction = self._current_direction
        self._queued_direction = (0, 0)
        self._lock_movement_for_spawn = True

        for item in self._items:
            item.scale = (
                (cell_size * ITEM_CELL_FRACTION)
                / max(1.0, float(item.texture.width))
            )
            item.center_x, item.center_y = self._maze_display.cell_center(
                self.window.width,
                self.window.height,
                self._item_cell_x,
                self._item_cell_y,
            )

    def _keep_player_on_lane(self) -> None:
        """Snap the perpendicular axis to the maze cell center line."""
        if self.window is None:
            return

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        if self._current_direction[0] != 0:
            self._player.center_y = _nearest_cell_center(
                self._player.center_y,
                offset_y,
                cell_size,
            )
        elif self._current_direction[1] != 0:
            self._player.center_x = _nearest_cell_center(
                self._player.center_x,
                offset_x,
                cell_size,
            )

    def _current_cell_value(self) -> int:
        """Return wall flags for the maze cell currently containing the player."""
        if self.window is None:
            return int(self._maze_grid[self._player_cell_y][self._player_cell_x])

        cell_size, offset_x, offset_y = self._maze_display.layout_for_window(
            self.window.width,
            self.window.height,
        )
        cell_x = _nearest_cell_index(self._player.center_x, offset_x, cell_size)
        cell_y = _nearest_cell_index(
            self.window.height - self._player.center_y,
            offset_y,
            cell_size,
        )
        cell_x = max(0, min(self._maze_display.cols - 1, cell_x))
        cell_y = max(0, min(self._maze_display.rows - 1, cell_y))
        return int(self._maze_grid[cell_y][cell_x])

    def _rebuild_wall_colliders(self) -> None:
        """Recreate collision sprites so walls match the current maze layout."""
        if self.window is None:
            return

        walls: arcade.SpriteList = arcade.SpriteList(use_spatial_hash=True)
        for center_x, center_y, width, height in self._maze_display.wall_colliders(
            self.window.width,
            self.window.height,
        ):
            wall = arcade.SpriteSolidColor(
                max(1, round(width)),
                max(1, round(height)),
                color=(0, 0, 0, 0),
            )
            wall.center_x = center_x
            wall.center_y = center_y
            walls.append(wall)

        self._walls = walls
        self._physics_engine = arcade.PhysicsEngineSimple(self._player, self._walls)
