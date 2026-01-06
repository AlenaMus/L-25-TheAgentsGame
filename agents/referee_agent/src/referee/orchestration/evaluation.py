"""
Number drawing and winner evaluation.

Draws cryptographic random number and determines match outcome.
"""

from typing import Dict
from ..game_logic import GameState, GameStateMachine, draw_number, determine_winner
from ..utils import logger


async def draw_and_evaluate(
    match_params: Dict,
    game: GameStateMachine,
    choices: Dict[str, str]
) -> Dict:
    """
    Draw random number and determine winner.

    Args:
        match_params: Match parameters
        game: Game state machine
        choices: Player choices

    Returns:
        dict: Match result
    """
    match_id = match_params["match_id"]

    # Draw cryptographically random number
    drawn_number = draw_number()
    logger.info(
        "Number drawn",
        match_id=match_id,
        drawn_number=drawn_number
    )

    # Evaluate winner
    game.transition(GameState.EVALUATING)
    result = determine_winner(drawn_number, choices)
    game.transition(GameState.FINISHED)

    logger.info(
        "Winner determined",
        match_id=match_id,
        winner=result["winner_player_id"]
    )

    return result
