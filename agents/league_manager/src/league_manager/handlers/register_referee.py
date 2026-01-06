"""
Referee registration handler.

Handles REFEREE_REGISTER_REQUEST messages from referees.
"""

from datetime import datetime, timezone
from typing import Dict
from league_manager.registry.registry_manager import RegistryManager
from league_manager.utils.logger import logger


async def handle_register_referee(
    params: Dict,
    registry_manager: RegistryManager,
    league_id: str
) -> Dict:
    """
    Handle referee registration request.

    Args:
        params: Request parameters containing referee_meta
        registry_manager: Registry manager instance
        league_id: League identifier

    Returns:
        REFEREE_REGISTER_RESPONSE message

    Message Flow:
        Request: REFEREE_REGISTER_REQUEST
        Response: REFEREE_REGISTER_RESPONSE (ACCEPTED or REJECTED)

    Example Request:
        {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_REQUEST",
            "sender": "referee:alpha",
            "timestamp": "20250115T10:00:00Z",
            "conversation_id": "convrefalphareg001",
            "referee_meta": {
                "display_name": "Referee Alpha",
                "contact_endpoint": "http://localhost:8001/mcp",
                "max_concurrent_matches": 2,
                "game_types": ["even_odd"],
                "version": "1.0.0"
            }
        }

    Example Response (Success):
        {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_RESPONSE",
            "sender": "league_manager",
            "timestamp": "20250115T10:00:01Z",
            "conversation_id": "convrefalphareg001",
            "status": "ACCEPTED",
            "referee_id": "REF01",
            "auth_token": "tok_refref01_xyz789abc123",
            "league_id": "league_2025_even_odd"
        }
    """
    logger.info("Referee registration request received", params=params)

    # Extract referee metadata
    referee_meta = params.get("referee_meta", {})
    display_name = referee_meta.get("display_name", "Unknown Referee")
    endpoint = referee_meta.get("contact_endpoint")
    max_concurrent = referee_meta.get("max_concurrent_matches", 2)
    game_types = referee_meta.get("game_types", ["even_odd"])
    version = referee_meta.get("version", "1.0.0")

    # Validate required fields
    if not endpoint:
        logger.warning("Referee registration rejected: missing contact_endpoint")
        return _create_rejection_response(
            params,
            "Missing required field: contact_endpoint"
        )

    # Register referee
    try:
        referee_id, auth_token = registry_manager.register_referee(
            display_name=display_name,
            endpoint=endpoint,
            max_concurrent_matches=max_concurrent,
            game_types=game_types,
            version=version
        )
    except ValueError as e:
        logger.warning(f"Referee registration rejected: {str(e)}")
        return _create_rejection_response(params, str(e))

    # Create success response
    response = {
        "protocol": "league.v2",
        "message_type": "REFEREE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params.get("conversation_id", "conv_unknown"),
        "status": "ACCEPTED",
        "referee_id": referee_id,
        "auth_token": auth_token,
        "league_id": league_id
    }

    logger.info(
        "Referee registration accepted",
        referee_id=referee_id,
        display_name=display_name
    )

    return response


def _create_rejection_response(params: Dict, reason: str) -> Dict:
    """Create a REJECTED registration response."""
    return {
        "protocol": "league.v2",
        "message_type": "REFEREE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params.get("conversation_id", "conv_unknown"),
        "status": "REJECTED",
        "reason": reason
    }


__all__ = ["handle_register_referee"]
