"""
Player registration handler.

Handles LEAGUE_REGISTER_REQUEST from players.
"""

import secrets
from datetime import datetime, timezone
from typing import Dict
from ..utils.logger import logger


async def register_player(params: Dict, agent_registry, standings_calc) -> Dict:
    """
    Register a player and assign ID + token.

    Args:
        params: Registration request parameters
        agent_registry: Agent registry instance
        standings_calc: Standings calculator instance

    Returns:
        Registration response

    Example:
        >>> result = await register_player(params, registry, calc)
        >>> assert result["status"] == "ACCEPTED"
    """
    player_meta = params.get("player_meta", {})
    endpoint = player_meta.get("contact_endpoint", "")

    # Check if player already registered by endpoint
    existing_player = agent_registry.find_player_by_endpoint(endpoint)
    if existing_player:
        logger.info(
            "Player re-registration - returning existing credentials",
            player_id=existing_player["player_id"],
            endpoint=endpoint
        )
        return {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_RESPONSE",
            "sender": "league_manager",
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
            "status": "ACCEPTED",
            "player_id": existing_player["player_id"],
            "auth_token": existing_player["auth_token"],
            "league_id": "league_2025_even_odd"
        }

    # Check capacity
    if agent_registry.player_count() >= 50:
        logger.warning("Player registration rejected - league full")
        return {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_RESPONSE",
            "status": "REJECTED",
            "rejection_reason": "League full"
        }

    # Generate player ID
    player_id = f"P{agent_registry.player_count() + 1:02d}"

    # Generate auth token
    auth_token = f"tok_player_{player_id}_{secrets.token_urlsafe(32)}"

    # Store player
    agent_registry.add_player(
        player_id=player_id,
        display_name=player_meta.get("display_name", f"Player {player_id}"),
        endpoint=endpoint,
        game_types=player_meta.get("game_types", ["even_odd"]),
        version=player_meta.get("version", "1.0.0"),
        auth_token=auth_token
    )

    # Initialize in standings
    standings_calc.add_player(player_id, player_meta.get("display_name", f"Player {player_id}"))

    logger.info(
        "Player registered",
        player_id=player_id,
        display_name=player_meta.get("display_name")
    )

    return {
        "protocol": "league.v2",
        "message_type": "LEAGUE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        "status": "ACCEPTED",
        "player_id": player_id,
        "auth_token": auth_token,
        "league_id": "league_2025_even_odd"
    }
