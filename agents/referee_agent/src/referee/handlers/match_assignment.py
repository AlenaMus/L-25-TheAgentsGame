"""
Match assignment handler.

Receives match assignments from League Manager and starts
game orchestration.
"""

import asyncio
from typing import Dict
from ..game_orchestrator import orchestrate_game
from ..utils.logger import logger


async def handle_match_assignment(params: Dict) -> Dict:
    """
    Handle match assignment from League Manager.

    Creates game state and starts orchestration in background.

    Args:
        params: Match assignment parameters:
            - match_id: Match identifier
            - round_id: Round identifier
            - player_A_id: Player A identifier
            - player_B_id: Player B identifier
            - player_A_endpoint: Player A HTTP endpoint
            - player_B_endpoint: Player B HTTP endpoint

    Returns:
        dict: Acknowledgment with match_id

    Example:
        >>> params = {
        ...     "match_id": "R1M1",
        ...     "round_id": "1",
        ...     "player_A_id": "P01",
        ...     "player_B_id": "P02",
        ...     "player_A_endpoint": "http://localhost:8101/mcp",
        ...     "player_B_endpoint": "http://localhost:8102/mcp"
        ... }
        >>> result = await handle_match_assignment(params)
        >>> result["status"]
        "accepted"
    """
    match_id = params["match_id"]

    logger.info(
        "Match assignment received",
        match_id=match_id,
        round_id=params["round_id"],
        player_A=params["player_A_id"],
        player_B=params["player_B_id"]
    )

    # Start game orchestration in background
    asyncio.create_task(orchestrate_game(params))

    return {
        "protocol": "league.v2",
        "message_type": "MATCH_ASSIGNMENT_ACK",
        "status": "accepted",
        "match_id": match_id
    }
