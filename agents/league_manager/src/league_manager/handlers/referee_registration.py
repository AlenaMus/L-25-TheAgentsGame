"""
Referee registration handler.

Handles REFEREE_REGISTER_REQUEST from referees.
"""

import secrets
from datetime import datetime, timezone
from typing import Dict
from ..utils.logger import logger


async def register_referee(params: Dict, agent_registry) -> Dict:
    """
    Register a referee and assign ID + token.

    Args:
        params: Registration request parameters
        agent_registry: Agent registry instance

    Returns:
        Registration response
    """
    referee_meta = params.get("referee_meta", {})
    endpoint = referee_meta.get("contact_endpoint", "")

    # Check if referee already registered by endpoint
    existing_referee = agent_registry.find_referee_by_endpoint(endpoint)
    if existing_referee:
        logger.info(
            "Referee re-registration - returning existing credentials",
            referee_id=existing_referee["referee_id"],
            endpoint=endpoint
        )
        return {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_RESPONSE",
            "sender": "league_manager",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "status": "ACCEPTED",
            "referee_id": existing_referee["referee_id"],
            "auth_token": existing_referee["auth_token"],
            "league_id": "league_2025_even_odd"
        }

    # Check capacity
    if agent_registry.referee_count() >= 10:
        logger.warning("Referee registration rejected - max referees")
        return {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_RESPONSE",
            "status": "REJECTED",
            "rejection_reason": "Maximum referees reached"
        }

    # Generate referee ID
    referee_id = f"REF{agent_registry.referee_count() + 1:02d}"

    # Generate auth token
    auth_token = f"tok_referee_{referee_id}_{secrets.token_urlsafe(32)}"

    # Store referee
    agent_registry.add_referee(
        referee_id=referee_id,
        display_name=referee_meta.get("display_name", f"Referee {referee_id}"),
        endpoint=endpoint,
        game_types=referee_meta.get("supported_games", ["even_odd"]),
        max_concurrent=referee_meta.get("max_concurrent_games", 5),
        version=referee_meta.get("version", "1.0.0"),
        auth_token=auth_token
    )

    logger.info(
        "Referee registered",
        referee_id=referee_id,
        display_name=referee_meta.get("display_name")
    )

    return {
        "protocol": "league.v2",
        "message_type": "REFEREE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "status": "ACCEPTED",
        "referee_id": referee_id,
        "auth_token": auth_token,
        "league_id": "league_2025_even_odd"
    }
