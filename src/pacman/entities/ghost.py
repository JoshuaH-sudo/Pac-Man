"""Ghost enemy entity."""

from __future__ import annotations

from collections import deque
from pathlib import Path
import random
from typing import Sequence

from pacman.entities.entity import Entity
from pacman.core import Direction, choose_initial_direction, direction_is_open

ASSETS_DIR = Path(__file__).resolve().parents[2] / "assets" / "sprites"


class Ghost(Entity):
    """Ghost entity with lane-aligned movement and target-tile decisions.

    Movement is intentionally split into small steps:
    1. Detect open exits in the current maze cell.
    2. Keep moving to cell center when needed to avoid corner jitter.
    3. At a center/intersection, pick the next direction.
    4. Apply velocity and snap to lane to stay corridor-aligned.

    Direction tuples use world-space signs: (0, 1) means visually "up".
    Maze rows increase downward, so moving up maps to row - 1.
    """

    def __init__(
        self,
        sprite_sheet_name: str,
        center_x: float,
        center_y: float,
        speed: float,
        scale: float = 1.0,
    ) -> None:
        super().__init__(
            sprite_sheet_path=ASSETS_DIR / sprite_sheet_name,
            center_x=center_x,
            center_y=center_y,
            scale=scale,
            rows=2,
            columns=1,
        )
        self.define_animation("idle", [(0, 0)])
        self.define_animation("vulnerable", [(1, 0)])
        self.set_animation_frame("idle")

        self._speed = speed
        self._direction: Direction = (0, 0)
        self._is_vulnerable = False

    def set_vulnerable(self, is_vulnerable: bool) -> None:
        """Switch between idle and vulnerability ghost sprite rows.

        This only affects visuals; movement logic is unchanged.
        """
        if self._is_vulnerable == is_vulnerable:
            return

        self._is_vulnerable = is_vulnerable
        self.set_animation_frame("vulnerable" if is_vulnerable else "idle")

    def move(self, horizontal: int, vertical: int) -> None:
        """Set movement direction for the current update loop."""
        self.change_x = horizontal * self._speed
        self.change_y = vertical * self._speed

    def set_speed(self, speed: float) -> None:
        """Update movement speed in pixels per frame."""
        self._speed = speed

    def set_spawn_direction(self, cell_value: int) -> None:
        """Reset movement heading from the ghost's spawn cell exits."""
        self._direction = choose_initial_direction(cell_value)

    @staticmethod
    def _manhattan_distance(
        cell_x1: int,
        cell_y1: int,
        cell_x2: int,
        cell_y2: int,
    ) -> int:
        """Return Manhattan distance between two maze cells."""
        return abs(cell_x1 - cell_x2) + abs(cell_y1 - cell_y2)

    def _closest_direction_to_target(
        self,
        current_cell_x: int,
        current_cell_y: int,
        target_cell_x: int,
        target_cell_y: int,
        open_directions: list[Direction],
        maze_grid: Sequence[Sequence[int]] | None = None,
    ) -> Direction:
        """Choose legal direction whose next tile is closest to target.

        Reversing direction is excluded unless it is the only legal option.
        For each candidate, we score the resulting next tile by path distance
        (BFS) when a maze grid is available, otherwise by Manhattan distance.
        """
        reverse_direction = (-self._direction[0], -self._direction[1])
        candidate_directions = [
            direction
            for direction in open_directions
            if direction != reverse_direction
        ]
        if not candidate_directions:
            candidate_directions = open_directions

        best_direction = candidate_directions[0]
        best_distance = self._direction_distance_to_target(
            next_cell_x=current_cell_x + best_direction[0],
            next_cell_y=current_cell_y - best_direction[1],
            target_cell_x=target_cell_x,
            target_cell_y=target_cell_y,
            maze_grid=maze_grid,
        )
        for direction in candidate_directions[1:]:
            distance = self._direction_distance_to_target(
                next_cell_x=current_cell_x + direction[0],
                next_cell_y=current_cell_y - direction[1],
                target_cell_x=target_cell_x,
                target_cell_y=target_cell_y,
                maze_grid=maze_grid,
            )
            if distance < best_distance:
                best_distance = distance
                best_direction = direction

        return best_direction

    @staticmethod
    def _direction_distance_to_target(
        next_cell_x: int,
        next_cell_y: int,
        target_cell_x: int,
        target_cell_y: int,
        maze_grid: Sequence[Sequence[int]] | None,
    ) -> int:
        """Score a candidate next cell by distance to the target tile.

        Path distance is preferred because Manhattan distance can be misleading
        in mazes with walls. If no path can be found (or no grid is provided),
        Manhattan distance is used as a deterministic fallback.
        """
        if maze_grid is None:
            return Ghost._manhattan_distance(
                next_cell_x,
                next_cell_y,
                target_cell_x,
                target_cell_y,
            )

        shortest_path = Ghost._shortest_path_distance(
            start_cell_x=next_cell_x,
            start_cell_y=next_cell_y,
            target_cell_x=target_cell_x,
            target_cell_y=target_cell_y,
            maze_grid=maze_grid,
        )
        if shortest_path is None:
            # Fallback keeps deterministic behavior in disconnected regions.
            return Ghost._manhattan_distance(
                next_cell_x,
                next_cell_y,
                target_cell_x,
                target_cell_y,
            )
        return shortest_path

    @staticmethod
    def _shortest_path_distance(
        start_cell_x: int,
        start_cell_y: int,
        target_cell_x: int,
        target_cell_y: int,
        maze_grid: Sequence[Sequence[int]],
    ) -> int | None:
        """Return BFS shortest path distance between two maze cells.

        Returns `None` when either coordinate is out of bounds or when no path
        is reachable through open cell exits.
        """
        if start_cell_x == target_cell_x and start_cell_y == target_cell_y:
            return 0

        row_count = len(maze_grid)
        col_count = len(maze_grid[0]) if row_count > 0 else 0
        if row_count == 0 or col_count == 0:
            return None

        if (
            start_cell_x < 0
            or start_cell_x >= col_count
            or start_cell_y < 0
            or start_cell_y >= row_count
            or target_cell_x < 0
            or target_cell_x >= col_count
            or target_cell_y < 0
            or target_cell_y >= row_count
        ):
            return None

        visited: set[tuple[int, int]] = {(start_cell_x, start_cell_y)}
        queue: deque[tuple[int, int, int]] = deque(
            [(start_cell_x, start_cell_y, 0)]
        )

        while queue:
            current_x, current_y, distance = queue.popleft()
            cell_value = int(maze_grid[current_y][current_x])

            for direction in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                if not direction_is_open(cell_value, direction):
                    continue
                next_x = current_x + direction[0]
                next_y = current_y - direction[1]
                if (
                    next_x < 0
                    or next_x >= col_count
                    or next_y < 0
                    or next_y >= row_count
                    or (next_x, next_y) in visited
                ):
                    continue

                if next_x == target_cell_x and next_y == target_cell_y:
                    return distance + 1

                visited.add((next_x, next_y))
                queue.append((next_x, next_y, distance + 1))

        return None

    @staticmethod
    def _open_directions(cell_value: int) -> list[Direction]:
        """Return every direction that is open from the current maze cell.

        The bitmask in `cell_value` encodes which edges are blocked.
        """
        return [
            direction
            for direction in ((0, 1), (1, 0), (0, -1), (-1, 0))
            if direction_is_open(cell_value, direction)
        ]

    @staticmethod
    def _alignment_tolerance(cell_size: float) -> float:
        """Return tolerance used to treat the ghost as center-aligned.

        A small tolerance helps avoid floating-point noise causing indecision
        right around tile centers.
        """
        return max(0.5, cell_size * 0.03)

    def _is_aligned_to_center(
        self,
        center_x: float,
        center_y: float,
        tolerance: float,
    ) -> bool:
        """Return True when ghost is close enough to tile center."""
        return (
            abs(self.center_x - center_x) <= tolerance
            and abs(self.center_y - center_y) <= tolerance
        )

    def _distance_to_center_along_heading(
        self,
        center_x: float,
        center_y: float,
    ) -> float:
        """Project remaining distance to center onto current heading axis.

        Positive output means continuing in the current direction moves toward
        center; negative means the center is already behind the ghost.
        """
        if self._direction[0] != 0:
            return (center_x - self.center_x) * self._direction[0]
        if self._direction[1] != 0:
            return (center_y - self.center_y) * self._direction[1]
        return 0.0

    def _continue_to_center_if_needed(
        self,
        cell_value: int,
        center_x: float,
        center_y: float,
        cell_size: float,
        offset_x: float,
        offset_y: float,
        aligned_to_center: bool,
        alignment_tolerance: float,
    ) -> bool:
        """Keep moving to center when heading just became blocked.

        This prevents abrupt stop-turn behavior before the center point,
        which otherwise looks like oscillation at tight corners.

        Returns `True` when movement for this tick is already handled.
        """
        if (
            self._direction == (0, 0)
            or direction_is_open(cell_value, self._direction)
            or aligned_to_center
        ):
            return False

        # Prevent corner lockups: finish the current lane until the center.
        distance_to_center = self._distance_to_center_along_heading(
            center_x,
            center_y,
        )
        if distance_to_center > alignment_tolerance:
            self._apply_direction(
                direction=self._direction,
                cell_size=cell_size,
                offset_x=offset_x,
                offset_y=offset_y,
            )
            return True

        self.center_x = center_x
        self.center_y = center_y
        return False

    def _select_targeted_or_random_direction(
        self,
        open_directions: list[Direction],
        maze_grid: Sequence[Sequence[int]] | None,
        ghost_cell_x: int | None,
        ghost_cell_y: int | None,
        target_cell_x: int | None,
        target_cell_y: int | None,
    ) -> Direction:
        """Choose next direction from either target or roaming behavior.

        If both ghost and target tiles are known, this uses the target-tile
        mechanic. Otherwise, it falls back to roaming movement so the ghost can
        still move in contexts where tile coordinates are unavailable.
        """
        # Classic rule: at intersections, pick the legal move that gets closest
        # to the target tile, excluding reverse unless forced.
        if (
            ghost_cell_x is not None
            and ghost_cell_y is not None
            and target_cell_x is not None
            and target_cell_y is not None
        ):
            return self._closest_direction_to_target(
                current_cell_x=ghost_cell_x,
                current_cell_y=ghost_cell_y,
                target_cell_x=target_cell_x,
                target_cell_y=target_cell_y,
                open_directions=open_directions,
                maze_grid=maze_grid,
            )
        return self._select_random_direction(open_directions)

    def _select_random_direction(self, open_directions: list[Direction]) -> Direction:
        """Return roaming direction, preferring not to reverse when possible.

        The current direction is kept with moderate probability so ghosts look
        less jittery and do not over-turn at every intersection.
        """
        reverse_direction = (-self._direction[0], -self._direction[1])
        non_reverse_directions = [
            direction
            for direction in open_directions
            if direction != reverse_direction
        ]
        candidate_directions = (
            non_reverse_directions
            if non_reverse_directions
            else open_directions
        )
        if self._direction in candidate_directions and random.random() < 0.65:
            return self._direction
        return random.choice(candidate_directions)

    @staticmethod
    def _ensure_direction_is_open(
        direction: Direction,
        cell_value: int,
    ) -> Direction:
        """Validate selected direction against cell exits.

        Returns `(0, 0)` if the move is currently blocked.
        """
        if direction != (0, 0) and not direction_is_open(cell_value, direction):
            return (0, 0)
        return direction

    def _apply_direction(
        self,
        direction: Direction,
        cell_size: float,
        offset_x: float,
        offset_y: float,
    ) -> None:
        """Persist direction and apply velocity and lane alignment.

        Lane snapping keeps the ghost anchored to maze corridors even when
        floating-point drift accumulates over many frames.
        """
        self._direction = direction
        self.move(direction[0], direction[1])
        self.snap_to_lane(
            direction=self._direction,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
            max_alignment_step=max(abs(self.change_x), abs(self.change_y)),
        )

    def update_maze_movement(
        self,
        cell_value: int,
        center_x: float,
        center_y: float,
        cell_size: float,
        offset_x: float,
        offset_y: float,
        maze_grid: Sequence[Sequence[int]] | None = None,
        ghost_cell_x: int | None = None,
        ghost_cell_y: int | None = None,
        target_cell_x: int | None = None,
        target_cell_y: int | None = None,
    ) -> None:
        """Resolve one movement tick using center-based intersection logic.

        Args:
            cell_value: Maze bitmask for the ghost's current tile.
            center_x: World-space x of current tile center.
            center_y: World-space y of current tile center.
            cell_size: Tile size in pixels.
            offset_x: Maze x offset in world-space pixels.
            offset_y: Maze y offset in world-space pixels.
            maze_grid: Optional full maze grid for BFS path scoring.
            ghost_cell_x: Optional ghost tile x index.
            ghost_cell_y: Optional ghost tile y index.
            target_cell_x: Optional target tile x index.
            target_cell_y: Optional target tile y index.
        """
        open_directions = self._open_directions(cell_value)
        if not open_directions:
            self._apply_direction(
                direction=(0, 0),
                cell_size=cell_size,
                offset_x=offset_x,
                offset_y=offset_y,
            )
            return

        alignment_tolerance = self._alignment_tolerance(cell_size)
        aligned_to_center = self._is_aligned_to_center(
            center_x=center_x,
            center_y=center_y,
            tolerance=alignment_tolerance,
        )

        if self._continue_to_center_if_needed(
            cell_value=cell_value,
            center_x=center_x,
            center_y=center_y,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
            aligned_to_center=aligned_to_center,
            alignment_tolerance=alignment_tolerance,
        ):
            return

        aligned_to_center = self._is_aligned_to_center(
            center_x=center_x,
            center_y=center_y,
            tolerance=alignment_tolerance,
        )

        next_direction = self._direction
        if aligned_to_center:
            # Decision points happen at centers/intersections.
            self.center_x = center_x
            self.center_y = center_y
            next_direction = self._select_targeted_or_random_direction(
                open_directions=open_directions,
                maze_grid=maze_grid,
                ghost_cell_x=ghost_cell_x,
                ghost_cell_y=ghost_cell_y,
                target_cell_x=target_cell_x,
                target_cell_y=target_cell_y,
            )
        else:
            # Between centers, keep heading unchanged to avoid diagonal corner cuts.
            if self._direction not in open_directions:
                next_direction = (0, 0)

        next_direction = self._ensure_direction_is_open(
            direction=next_direction,
            cell_value=cell_value,
        )
        self._apply_direction(
            direction=next_direction,
            cell_size=cell_size,
            offset_x=offset_x,
            offset_y=offset_y,
        )

    def update_animation(self, delta_time: float = 1 / 60) -> None:
        """Ghost sprites are static for now; animation support comes later."""
        del delta_time
