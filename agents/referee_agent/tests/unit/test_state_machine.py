"""
Unit tests for game state machine.

Tests state transitions and validation logic.
"""

import pytest
from referee.game_logic import GameState, GameStateMachine


def test_state_machine_initial_state():
    """Test state machine starts in WAITING_FOR_PLAYERS state."""
    game = GameStateMachine("R1M1")
    assert game.state == GameState.WAITING_FOR_PLAYERS
    assert game.match_id == "R1M1"
    assert len(game.history) == 1


def test_valid_state_transition():
    """Test valid state transitions succeed."""
    game = GameStateMachine("R1M1")

    # WAITING_FOR_PLAYERS -> COLLECTING_CHOICES
    game.transition(GameState.COLLECTING_CHOICES)
    assert game.state == GameState.COLLECTING_CHOICES

    # COLLECTING_CHOICES -> DRAWING_NUMBER
    game.transition(GameState.DRAWING_NUMBER)
    assert game.state == GameState.DRAWING_NUMBER

    # DRAWING_NUMBER -> EVALUATING
    game.transition(GameState.EVALUATING)
    assert game.state == GameState.EVALUATING

    # EVALUATING -> FINISHED
    game.transition(GameState.FINISHED)
    assert game.state == GameState.FINISHED


def test_invalid_state_transition():
    """Test invalid state transitions raise ValueError."""
    game = GameStateMachine("R1M1")

    # Cannot jump from WAITING_FOR_PLAYERS to FINISHED
    with pytest.raises(ValueError):
        game.transition(GameState.FINISHED)


def test_abort_from_any_state():
    """Test game can be aborted from any state."""
    game = GameStateMachine("R1M1")

    # Can abort from WAITING_FOR_PLAYERS
    game.transition(GameState.ABORTED)
    assert game.state == GameState.ABORTED

    # Cannot transition from ABORTED
    game2 = GameStateMachine("R1M2")
    game2.transition(GameState.COLLECTING_CHOICES)
    game2.transition(GameState.ABORTED)
    with pytest.raises(ValueError):
        game2.transition(GameState.DRAWING_NUMBER)


def test_can_transition_check():
    """Test can_transition validation method."""
    game = GameStateMachine("R1M1")

    # Can transition to COLLECTING_CHOICES
    assert game.can_transition(GameState.COLLECTING_CHOICES)

    # Cannot transition to FINISHED
    assert not game.can_transition(GameState.FINISHED)

    # Can transition to ABORTED
    assert game.can_transition(GameState.ABORTED)


def test_history_tracking():
    """Test state transition history is tracked."""
    game = GameStateMachine("R1M1")

    game.transition(GameState.COLLECTING_CHOICES)
    game.transition(GameState.DRAWING_NUMBER)

    # Should have 3 entries (initial + 2 transitions)
    assert len(game.history) == 3
    assert game.history[0][0] == GameState.WAITING_FOR_PLAYERS
    assert game.history[1][0] == GameState.COLLECTING_CHOICES
    assert game.history[2][0] == GameState.DRAWING_NUMBER
