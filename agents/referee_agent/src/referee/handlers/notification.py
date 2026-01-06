"""
Player notification handler.

Sends match results to players.
"""

from typing import Dict
from ..mcp_client import MCPClient
from ..utils.logger import logger
from ..storage.agent_registry import AgentRegistry


async def notify_players(
    match_id: str,
    result: Dict,
    agent_registry: AgentRegistry
) -> None:
    """
    Notify both players of match result.

    Args:
        match_id: Match identifier
        result: Match result from determine_winner
        agent_registry: Agent registry for player endpoints
    """
    client = MCPClient(timeout=5)
    try:
        choices = result["choices"]
        player_ids = list(choices.keys())

        notification = {
            "match_id": match_id,
            "winner_id": result["winner_player_id"],
            "drawn_number": result["drawn_number"],
            "choices": choices
        }

        # Notify all players
        for player_id in player_ids:
            player = agent_registry.get_player(player_id)
            if player:
                try:
                    await client.call_tool(
                        player["endpoint"],
                        "notify_match_result",
                        notification
                    )
                except Exception as e:
                    logger.warning(
                        "Player notification failed",
                        player_id=player_id,
                        error=str(e)
                    )

    except Exception as e:
        logger.warning("Notification error", error=str(e))
    finally:
        await client.close()
