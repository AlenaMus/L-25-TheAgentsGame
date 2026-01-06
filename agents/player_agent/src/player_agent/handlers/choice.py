"""
Handler for parity choice tool.

Makes even/odd choice based on strategy.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from player_agent.utils.logger import logger
from player_agent.strategies import RandomStrategy


async def choose_parity(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Choose parity (even or odd) based on strategy.

    Must respond within 30 seconds (enforced by timeout decorator).

    Args:
        params: CHOOSE_PARITY_CALL message parameters containing:
            - conversation_id: Conversation tracking ID
            - match_id: Match identifier
            - player_id: This player's ID
            - game_type: Game type (e.g., "even_odd")
            - context: Additional context with opponent_id, standings
            - deadline: UTC timestamp deadline

    Returns:
        dict: CHOOSE_PARITY_RESPONSE with:
            - protocol: Protocol version
            - message_type: "CHOOSE_PARITY_RESPONSE"
            - sender: This player's identifier
            - timestamp: Current UTC timestamp
            - conversation_id: Same as request
            - match_id: Same as request
            - player_id: This player's ID
            - parity_choice: "even" or "odd"

    Example:
        >>> result = await choose_parity({
        ...     "conversation_id": "convr1m1001",
        ...     "match_id": "R1M1",
        ...     "player_id": "P01"
        ... })
        >>> print(result["parity_choice"] in ["even", "odd"])
        True
    """
    match_id = params.get("match_id")
    player_id = params.get("player_id", "P01")
    context = params.get("context", {})
    opponent_id = context.get("opponent_id", "UNKNOWN")

    logger.info(
        "Parity choice requested",
        conversation_id=params.get("conversation_id"),
        match_id=match_id,
        opponent_id=opponent_id
    )

    # Initialize strategy (Phase 1: Random Strategy)
    # TODO: Phase 2 - Replace with adaptive strategy
    strategy = RandomStrategy()

    # Get opponent history (empty for now - Phase 2 will populate from storage)
    opponent_history = []

    # Get current standings from context
    standings = context.get("your_standings", {})

    # Make strategic choice
    choice = strategy.choose_parity(
        match_id=match_id,
        opponent_id=opponent_id,
        opponent_history=opponent_history,
        standings=standings
    )

    # Validate choice (defensive programming)
    if choice not in ["even", "odd"]:
        logger.error(
            f"Invalid choice generated: {choice}, defaulting to 'even'",
            match_id=match_id,
            strategy=strategy.get_name()
        )
        choice = "even"

    logger.info(
        "Parity choice made",
        conversation_id=params.get("conversation_id"),
        match_id=match_id,
        choice=choice,
        strategy=strategy.get_name()
    )

    # TODO: Use actual auth token
    auth_token = "tok_p01_temp"

    response = {
        "protocol": "league.v2",
        "message_type": "CHOOSE_PARITY_RESPONSE",
        "sender": f"player:{player_id}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params["conversation_id"],
        "auth_token": auth_token,
        "match_id": match_id,
        "player_id": player_id,
        "parity_choice": choice
    }

    return response
