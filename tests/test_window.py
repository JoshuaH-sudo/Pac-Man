"""Tests for maze wall rendering and movement geometry."""

from types import SimpleNamespace
from typing import Any, cast

from pacman.core import (
    CLOSED_EAST,
    CLOSED_NORTH,
    CLOSED_SOUTH,
    CLOSED_WEST,
    center_cell_index,
    choose_initial_direction,
    coerce_blocked_directions,
    direction_is_open,
    nearest_cell_center,
    nearest_cell_index,
    resolve_direction,
)
from pacman.maze import (
    MazeDisplay,
    build_corner_cells,
    build_item_cells,
    build_super_item_cells,
)
from pacman.game.game_view import GameView
from pacman.input import MovementController


def test_center_cell_index_prefers_discrete_middle_cell() -> None:
    """Maze spawn logic should always choose a valid center cell index."""
    assert center_cell_index(21) == 10
    assert center_cell_index(20) == 9


def test_choose_initial_direction_prefers_open_north_path() -> None:
    """Initial movement should select the first open direction for a cell."""
    assert choose_initial_direction(CLOSED_EAST | CLOSED_SOUTH) == (0, 1)


def test_direction_is_open_respects_wall_flags() -> None:
    """Blocked walls should reject direction requests immediately."""
    blocked_all_but_west = CLOSED_NORTH | CLOSED_EAST | CLOSED_SOUTH
    assert direction_is_open(blocked_all_but_west, (-1, 0))
    assert not direction_is_open(blocked_all_but_west, (0, 1))
    assert not direction_is_open(blocked_all_but_west, (1, 0))
    assert not direction_is_open(blocked_all_but_west, (0, -1))

    blocked_west = CLOSED_WEST
    assert not direction_is_open(blocked_west, (-1, 0))


def test_coerce_blocked_directions_stops_when_current_path_closes() -> None:
    """If current travel is blocked, movement should stop and clear intent."""
    blocked_north = CLOSED_NORTH
    current, desired = coerce_blocked_directions(
        current_direction=(0, 1),
        desired_direction=(0, 1),
        cell_value=blocked_north,
    )
    assert current == (0, 0)
    assert desired == (0, 0)


def test_coerce_blocked_directions_keeps_valid_new_direction() -> None:
    """A stationary player should resume only when desired direction is open."""
    open_north = CLOSED_EAST | CLOSED_SOUTH | CLOSED_WEST
    current, desired = coerce_blocked_directions(
        current_direction=(0, 0),
        desired_direction=(0, 1),
        cell_value=open_north,
    )
    assert current == (0, 0)
    assert desired == (0, 1)


def test_queued_direction_applies_when_open() -> None:
    """A queued turn should be promoted when the cell opens that direction."""
    blocked_north = CLOSED_NORTH
    assert not direction_is_open(blocked_north, (0, 1))

    open_north = CLOSED_EAST | CLOSED_SOUTH | CLOSED_WEST
    assert direction_is_open(open_north, (0, 1))


def test_nearest_cell_center_snaps_to_lane_center() -> None:
    """Lane snapping should align to the nearest maze center line."""
    snapped = nearest_cell_center(58.0, offset=10.0, cell_size=20.0)
    assert snapped == 60.0


def test_nearest_cell_index_uses_closest_cell_not_floor() -> None:
    """Cell lookup should prefer the nearest center around boundaries."""
    assert nearest_cell_index(58.0, offset=10.0, cell_size=20.0) == 2
    assert nearest_cell_index(51.0, offset=10.0, cell_size=20.0) == 2


def test_resolve_direction_turns_when_aligned() -> None:
    """A perpendicular turn should apply once the player is near lane center."""
    direction, center_x, center_y = resolve_direction(
        current_direction=(1, 0),
        desired_direction=(0, 1),
        center_x=60.0,
        center_y=59.0,
        cell_size=20.0,
        offset_x=10.0,
        offset_y=10.0,
    )
    assert direction == (0, 1)
    assert center_x == 60.0
    assert center_y == 60.0


def test_resolve_direction_does_not_turn_too_early() -> None:
    """Perpendicular turn should wait until the actor reaches corridor center."""
    direction, center_x, center_y = resolve_direction(
        current_direction=(1, 0),
        desired_direction=(0, 1),
        center_x=66.0,
        center_y=60.0,
        cell_size=20.0,
        offset_x=10.0,
        offset_y=10.0,
    )
    assert direction == (1, 0)
    assert center_x == 66.0
    assert center_y == 60.0


def test_resolve_direction_resumes_from_stop() -> None:
    """A stopped player should follow a valid desired direction immediately."""
    direction, center_x, center_y = resolve_direction(
        current_direction=(0, 0),
        desired_direction=(-1, 0),
        center_x=60.0,
        center_y=60.0,
        cell_size=20.0,
        offset_x=10.0,
        offset_y=10.0,
    )
    assert direction == (-1, 0)
    assert center_x == 60.0
    assert center_y == 60.0


def test_movement_controller_centers_on_blocked_stop() -> None:
    """Stopping at a dead-end should snap Pac-Man to the cell center."""
    controller = MovementController(initial_direction=(0, 1))

    direction, center_x, center_y, _ = controller.apply(
        player_center_x=103.2,
        player_center_y=146.7,
        cell_size=20.0,
        offset_x=10.0,
        offset_y=10.0,
        cell_value=0,
    )
    assert direction == (0, 0)
    assert center_x == 103.2
    assert center_y == 146.7

    direction, center_x, center_y, _ = controller.apply(
        player_center_x=103.2,
        player_center_y=146.7,
        cell_size=20.0,
        offset_x=10.0,
        offset_y=10.0,
        cell_value=CLOSED_NORTH,
    )
    assert direction == (0, 0)
    assert center_x == 100.0
    assert center_y == 140.0


def test_wall_colliders_create_vertical_barrier() -> None:
    """An east wall should produce a tall, narrow collision box."""
    colliders = MazeDisplay([[CLOSED_EAST]]).wall_colliders(200, 200)

    assert len(colliders) == 1
    _, _, width, height = colliders[0]
    assert width > 0
    assert height > 0
    assert height > width


def test_wall_colliders_create_horizontal_barrier() -> None:
    """A north wall should produce a wide, short collision box."""
    colliders = MazeDisplay([[CLOSED_NORTH]]).wall_colliders(200, 200)

    assert len(colliders) == 1
    _, _, width, height = colliders[0]
    assert width > 0
    assert height > 0
    assert width > height


def test_game_view_pacgums_skip_corners_and_fully_closed_cells() -> None:
    """Pacgums should fill non-corner cells except fully closed dead cells."""
    fully_closed = CLOSED_NORTH | CLOSED_EAST | CLOSED_SOUTH | CLOSED_WEST
    maze_grid = [
        [0, 0, 0],
        [0, fully_closed, 0],
        [0, 0, 0],
    ]

    item_cells = build_item_cells(maze_grid)

    assert len(item_cells) == 4


def test_build_corner_cells_returns_all_four_corners() -> None:
    """Ghost spawn helper should include each maze corner exactly once."""
    assert build_corner_cells(cols=4, rows=3) == (
        (0.0, 0.0),
        (3.0, 0.0),
        (0.0, 2.0),
        (3.0, 2.0),
    )


def test_build_super_item_cells_matches_ghost_corner_spawns() -> None:
    """Super pacgums should spawn at the same corner cells as ghosts."""
    maze_grid = [[0] * 10 for _ in range(10)]
    assert build_super_item_cells(maze_grid) == (
        (0.0, 0.0),
        (9.0, 0.0),
        (0.0, 9.0),
        (9.0, 9.0),
    )


def test_sync_entities_to_maze_respawns_ghosts_at_spawn() -> None:
    """Entity sync should use ghost respawn logic so eaten ghosts are restored."""

    class _StubMazeDisplay:
        cols = 3
        rows = 3

        @staticmethod
        def layout_for_window(width: int, height: int) -> tuple[float, float, float]:
            del width
            del height
            return 20.0, 0.0, 0.0

        @staticmethod
        def cell_center(
            width: int,
            height: int,
            cell_x: float,
            cell_y: float,
        ) -> tuple[float, float]:
            del width
            del height
            return cell_x * 10.0 + 5.0, cell_y * 10.0 + 5.0

    class _StubActor:
        def __init__(self) -> None:
            self.texture = SimpleNamespace(width=10)
            self.scale = 1.0
            self.center_x = 0.0
            self.center_y = 0.0
            self.speed: float | None = None

        def set_speed(self, speed: float) -> None:
            self.speed = speed

    class _StubMovement:
        def __init__(self) -> None:
            self.reset_direction: tuple[int, int] | None = None

        def reset(self, direction: tuple[int, int]) -> None:
            self.reset_direction = direction

    class _StubGhost(_StubActor):
        def __init__(self) -> None:
            super().__init__()
            self.respawn_calls: list[tuple[float, float, int]] = []

        def respawn(self, center_x: float, center_y: float, cell_value: int) -> None:
            self.respawn_calls.append((center_x, center_y, cell_value))

    view = cast(Any, object.__new__(GameView))
    view.window = SimpleNamespace(width=120, height=120)
    view._maze_display = _StubMazeDisplay()
    view._player_cell_x = 1
    view._player_cell_y = 1
    view._player = _StubActor()
    view._maze_grid = (
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0),
    )
    view._movement = _StubMovement()
    view._rebuild_wall_colliders = lambda: None
    view._items = []
    view._all_item_cells = ()
    ghost = _StubGhost()
    view._ghosts = [ghost]
    view._ghost_cells = ((2.0, 1.0),)

    GameView._sync_entities_to_maze(view)

    assert ghost.respawn_calls == [(25.0, 15.0, 0)]
