"""Tests for Pac-Man directional animation mapping."""

from pacman.entities.pacman import Pacman


def test_pacman_uses_directional_animation_rows() -> None:
    """Each movement direction should select the matching sprite row."""
    pacman = Pacman(center_x=0.0, center_y=0.0, speed=1.0)

    expected_frames = {
        (-1, 0): {0, 1, 2},
        (1, 0): {3, 4, 5},
        (0, 1): {6, 7, 8},
        (0, -1): {9, 10, 11},
    }

    for direction, frames in expected_frames.items():
        pacman.move(*direction)
        pacman.update_animation()
        assert pacman._animation.current_frame_index in frames

        pacman.update_animation()
        assert pacman._animation.current_frame_index in frames

        pacman.update_animation()
        assert pacman._animation.current_frame_index in frames


def test_pacman_keeps_last_facing_direction_when_stopped() -> None:
    """Stopping should preserve the last facing row instead of resetting."""
    pacman = Pacman(center_x=0.0, center_y=0.0, speed=1.0)

    pacman.move(1, 0)
    pacman.update_animation()
    moving_frame = pacman._animation.current_frame_index

    pacman.move(0, 0)
    pacman.update_animation()

    assert pacman._animation.current_frame_index == moving_frame
