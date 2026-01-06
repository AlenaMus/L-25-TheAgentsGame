"""
Player invitation handling.

Sends GAME_INVITATION to both players and validates acceptance.
"""

import asyncio
from typing import Dict
from ..game_logic import GameState, GameStateMachine
from ..mcp_client import MCPClient
from ..config import config
from ..utils import logger, get_utc_timestamp


async def send_invitations(
    client: MCPClient,
    match_params: Dict,
    game: GameStateMachine
) -> bool:
    """
    Send game invitations to both players.

    Args:
        client: MCP client
        match_params: Match parameters
        game: Game state machine

    Returns:
        bool: True if both players accepted, False otherwise
    """
    match_id = match_params["match_id"]
    logger.info("Sending invitations", match_id=match_id)

    # Prepare invitation messages
    invitation_A = {
        "protocol": "league.v2",
        "message_type": "GAME_INVITATION",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}001",
        "auth_token": config.auth_token or "",
        "league_id": config.league_id or "",
        "round_id": match_params["round_id"],
        "match_id": match_id,
        "game_type": "even_odd",
        "role_in_match": "PLAYER_A",
        "opponent_id": match_params["player_B_id"]
    }

    invitation_B = {**invitation_A}
    invitation_B["role_in_match"] = "PLAYER_B"
    invitation_B["opponent_id"] = match_params["player_A_id"]

    # Send invitations simultaneously with timeout
    try:
        results = await asyncio.gather(
            asyncio.wait_for(
                client.call_tool(
                    match_params["player_A_endpoint"],
                    "handle_game_invitation",
                    invitation_A
                ),
                timeout=config.invitation_timeout
            ),
            asyncio.wait_for(
                client.call_tool(
                    match_params["player_B_endpoint"],
                    "handle_game_invitation",
                    invitation_B
                ),
                timeout=config.invitation_timeout
            ),
            return_exceptions=True
        )

        # Check both accepted
        for i, result in enumerate(results):
            player_id = (match_params["player_A_id"] if i == 0
                        else match_params["player_B_id"])

            if isinstance(result, Exception):
                logger.error(
                    "Player invitation failed",
                    match_id=match_id,
                    player_id=player_id,
                    error=str(result)
                )
                game.transition(GameState.ABORTED)
                return False

            if not result.get("result", {}).get("accept", False):
                logger.warning(
                    "Player rejected invitation",
                    match_id=match_id,
                    player_id=player_id
                )
                game.transition(GameState.ABORTED)
                return False

        # Both accepted
        game.transition(GameState.COLLECTING_CHOICES)
        return True

    except asyncio.TimeoutError:
        logger.error("Invitation timeout", match_id=match_id)
        game.transition(GameState.ABORTED)
        return False
