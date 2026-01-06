"""
Handler for match result notification.

Receives and stores match results for learning.
"""

from typing import Dict, Any

from player_agent.utils.logger import logger


async def notify_match_result(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle match result notification from referee.

    No timeout constraint (fire-and-forget notification).

    Args:
        params: GAME_OVER message parameters containing:
            - conversation_id: Conversation tracking ID
            - match_id: Match identifier
            - game_type: Game type (e.g., "even_odd")
            - game_result: Result object with:
                - status: "WIN", "LOSS", or "DRAW"
                - winner_player_id: Winner ID (or null for draw)
                - drawn_number: Number that was drawn
                - number_parity: "even" or "odd"
                - choices: Dict of player choices
                - reason: Description of result

    Returns:
        dict: Acknowledgment response with:
            - acknowledged: Always True

    Example:
        >>> result = await notify_match_result({
        ...     "conversation_id": "convr1m1001",
        ...     "match_id": "R1M1",
        ...     "game_result": {
        ...         "winner_player_id": "P01",
        ...         "drawn_number": 8
        ...     }
        ... })
        >>> print(result["acknowledged"])
        True
    """
    match_id = params.get("match_id")
    game_result = params.get("game_result", {})
    winner_id = game_result.get("winner_player_id")
    drawn_number = game_result.get("drawn_number")

    logger.info(
        "Match result received",
        conversation_id=params.get("conversation_id"),
        match_id=match_id,
        winner=winner_id,
        drawn_number=drawn_number,
        status=game_result.get("status")
    )

    # TODO: Implement game history storage
    # For now, just log the result

    # Extract opponent information
    choices = game_result.get("choices", {})
    player_id = params.get("player_id", "P01")

    # Determine opponent
    opponent_id = None
    my_choice = None
    opponent_choice = None

    for pid, choice in choices.items():
        if pid == player_id:
            my_choice = choice
        else:
            opponent_id = pid
            opponent_choice = choice

    logger.info(
        "Match details",
        match_id=match_id,
        opponent_id=opponent_id,
        my_choice=my_choice,
        opponent_choice=opponent_choice,
        drawn_number=drawn_number
    )

    # TODO: Store match record in history
    # TODO: Update opponent profile

    logger.info(
        "Match result acknowledged",
        match_id=match_id
    )

    return {"acknowledged": True}
