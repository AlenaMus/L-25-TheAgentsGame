"""
Game state machine for match orchestration.

Manages state transitions during a match and ensures
only valid transitions occur.
"""

from enum import Enum
from datetime import datetime
from typing import List, Tuple
from ..utils.logger import logger


class GameState(Enum):
    """
    Possible states during a game match.

    States:
        WAITING_FOR_PLAYERS: Waiting for both players to accept invitation
        COLLECTING_CHOICES: Collecting parity choices from both players
        DRAWING_NUMBER: Drawing random number
        EVALUATING: Determining winner
        FINISHED: Match completed successfully
        ABORTED: Match aborted due to error/timeout
    """
    WAITING_FOR_PLAYERS = "waiting_for_players"
    COLLECTING_CHOICES = "collecting_choices"
    DRAWING_NUMBER = "drawing_number"
    EVALUATING = "evaluating"
    FINISHED = "finished"
    ABORTED = "aborted"


class GameStateMachine:
    """
    State machine for game match lifecycle.

    Validates state transitions and maintains transition history
    for debugging and auditing.

    Attributes:
        match_id: Unique match identifier
        state: Current game state
        history: List of (state, timestamp) transitions

    Example:
        >>> game = GameStateMachine("R1M1")
        >>> game.transition(GameState.COLLECTING_CHOICES)
        >>> game.state
        <GameState.COLLECTING_CHOICES>
    """

    # Valid state transitions
    TRANSITIONS = {
        GameState.WAITING_FOR_PLAYERS: {
            GameState.COLLECTING_CHOICES,
            GameState.ABORTED
        },
        GameState.COLLECTING_CHOICES: {
            GameState.DRAWING_NUMBER,
            GameState.ABORTED
        },
        GameState.DRAWING_NUMBER: {GameState.EVALUATING},
        GameState.EVALUATING: {GameState.FINISHED},
        GameState.FINISHED: set(),
        GameState.ABORTED: set()
    }

    def __init__(self, match_id: str):
        """
        Initialize state machine.

        Args:
            match_id: Unique match identifier
        """
        self.match_id = match_id
        self.state = GameState.WAITING_FOR_PLAYERS
        self.history: List[Tuple[GameState, datetime]] = [
            (self.state, datetime.now())
        ]

    def transition(self, new_state: GameState) -> None:
        """
        Transition to new state with validation.

        Args:
            new_state: Target state

        Raises:
            ValueError: If transition is invalid
        """
        if new_state not in self.TRANSITIONS[self.state]:
            raise ValueError(
                f"Invalid transition: {self.state.value} -> {new_state.value}"
            )

        logger.info(
            "State transition",
            match_id=self.match_id,
            from_state=self.state.value,
            to_state=new_state.value
        )

        self.state = new_state
        self.history.append((self.state, datetime.now()))

    def can_transition(self, new_state: GameState) -> bool:
        """
        Check if transition to new state is valid.

        Args:
            new_state: Target state to check

        Returns:
            bool: True if transition is allowed
        """
        return new_state in self.TRANSITIONS[self.state]
