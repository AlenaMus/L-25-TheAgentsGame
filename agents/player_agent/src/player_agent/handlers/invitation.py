"""
Handler for game invitation tool.

Responds to GAME_INVITATION messages from referee.
"""

from datetime import datetime, timezone
from typing import Dict, Any

from player_agent.utils.logger import logger


async def handle_game_invitation(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle game invitation from referee.

    Must respond within 5 seconds (enforced by timeout decorator).

    Args:
        params: GAME_INVITATION message parameters containing:
            - conversation_id: Conversation tracking ID
            - match_id: Match identifier
            - opponent_id: Opponent player ID
            - league_id: League identifier
            - round_id: Round number
            - game_type: Game type (e.g., "even_odd")
            - role_in_match: Player role ("PLAYER_A" or "PLAYER_B")

    Returns:
        dict: GAME_JOIN_ACK response with:
            - protocol: Protocol version
            - message_type: "GAME_JOIN_ACK"
            - sender: This player's identifier
            - timestamp: Current UTC timestamp
            - conversation_id: Same as request
            - match_id: Same as request
            - player_id: This player's ID
            - arrival_timestamp: When invitation was received
            - accept: Always True (for now)

    Example:
        >>> result = await handle_game_invitation({
        ...     "conversation_id": "convr1m1001",
        ...     "match_id": "R1M1",
        ...     "opponent_id": "P02"
        ... })
        >>> print(result["accept"])
        True
    """
    logger.info(
        "Game invitation received",
        conversation_id=params.get("conversation_id"),
        match_id=params.get("match_id"),
        opponent_id=params.get("opponent_id"),
        round_id=params.get("round_id")
    )

    # TODO: Add configuration import when needed
    # For now, use placeholder values
    player_id = params.get("player_id", "P01")
    auth_token = "tok_p01_temp"  # TODO: Use actual auth token

    # Always accept invitations (required for tournament)
    response = {
        "protocol": "league.v2",
        "message_type": "GAME_JOIN_ACK",
        "sender": f"player:{player_id}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params["conversation_id"],
        "auth_token": auth_token,
        "match_id": params["match_id"],
        "player_id": player_id,
        "arrival_timestamp": datetime.now(timezone.utc).strftime(
            "%Y%m%dT%H%M%SZ"
        ),
        "accept": True
    }

    logger.info(
        "Game invitation accepted",
        conversation_id=params["conversation_id"],
        match_id=params["match_id"]
    )

    return response
