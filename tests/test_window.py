"""Tests for maze wall rendering and movement geometry."""

from pacman.constants import (
    CLOSED_EAST,
    CLOSED_NORTH,
    CLOSED_SOUTH,
    CLOSED_WEST,
)
from pacman.game_view import MazeDisplay
from pacman.utils import (
    center_cell_index,
    choose_initial_direction,
    coerce_blocked_directions,
    direction_is_open,
    nearest_cell_center,
    nearest_cell_index,
    resolve_player_direction,
)


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


def test_resolve_player_direction_turns_when_aligned() -> None:
    """A perpendicular turn should apply once the player is near lane center."""
    direction, center_x, center_y = resolve_player_direction(
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


def test_resolve_player_direction_resumes_from_stop() -> None:
    """A stopped player should follow a valid desired direction immediately."""
    direction, center_x, center_y = resolve_player_direction(
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