"""
Player registration handler.

Handles LEAGUE_REGISTER_REQUEST messages from players.
"""

from datetime import datetime, timezone
from typing import Dict
from league_manager.registry.registry_manager import RegistryManager
from league_manager.utils.logger import logger


async def handle_register_player(
    params: Dict,
    registry_manager: RegistryManager,
    league_id: str
) -> Dict:
    """
    Handle player registration request.

    Args:
        params: Request parameters containing player_meta
        registry_manager: Registry manager instance
        league_id: League identifier

    Returns:
        LEAGUE_REGISTER_RESPONSE message

    Message Flow:
        Request: LEAGUE_REGISTER_REQUEST
        Response: LEAGUE_REGISTER_RESPONSE (ACCEPTED or REJECTED)

    Example Request:
        {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_REQUEST",
            "sender": "player:alpha",
            "timestamp": "20250115T10:00:00Z",
            "conversation_id": "convplayeralphareg001",
            "player_meta": {
                "display_name": "Player Alpha",
                "contact_endpoint": "http://localhost:9001/mcp",
                "game_types": ["even_odd"],
                "version": "1.0.0"
            }
        }

    Example Response (Success):
        {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_RESPONSE",
            "sender": "league_manager",
            "timestamp": "20250115T10:00:01Z",
            "conversation_id": "convplayeralphareg001",
            "status": "ACCEPTED",
            "player_id": "P01",
            "auth_token": "tok_p01_xyz789abc123",
            "league_id": "league_2025_even_odd"
        }
    """
    logger.info("Player registration request received", params=params)

    # Extract player metadata
    player_meta = params.get("player_meta", {})
    display_name = player_meta.get("display_name", "Unknown Player")
    endpoint = player_meta.get("contact_endpoint")
    game_types = player_meta.get("game_types", ["even_odd"])
    version = player_meta.get("version", "1.0.0")

    # Validate required fields
    if not endpoint:
        logger.warning("Player registration rejected: missing contact_endpoint")
        return _create_rejection_response(
            params,
            "Missing required field: contact_endpoint"
        )

    # Register player
    try:
        player_id, auth_token = registry_manager.register_player(
            display_name=display_name,
            endpoint=endpoint,
            game_types=game_types,
            version=version
        )
    except ValueError as e:
        logger.warning(f"Player registration rejected: {str(e)}")
        return _create_rejection_response(params, str(e))

    # Create success response
    response = {
        "protocol": "league.v2",
        "message_type": "LEAGUE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params.get("conversation_id", "conv_unknown"),
        "status": "ACCEPTED",
        "player_id": player_id,
        "auth_token": auth_token,
        "league_id": league_id
    }

    logger.info(
        "Player registration accepted",
        player_id=player_id,
        display_name=display_name
    )

    return response


def _create_rejection_response(params: Dict, reason: str) -> Dict:
    """Create a REJECTED registration response."""
    return {
        "protocol": "league.v2",
        "message_type": "LEAGUE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params.get("conversation_id", "conv_unknown"),
        "status": "REJECTED",
        "reason": reason
    }


__all__ = ["handle_register_player"]
