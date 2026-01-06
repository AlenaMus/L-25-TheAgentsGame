"""
League Manager result reporter.

Reports match results to League Manager.
"""

from typing import Dict
from ..mcp_client import MCPClient
from ..utils.logger import logger
from ..config import config


async def report_to_league(match_id: str, result: Dict) -> None:
    """
    Report match result to League Manager.

    Args:
        match_id: Match identifier
        result: Match result from determine_winner

    Example:
        >>> await report_to_league("R1M1", result)
    """
    client = MCPClient(timeout=10)
    try:
        # Build player results
        players_result = {}
        winner_id = result["winner_player_id"]
        scores = result["scores"]

        for player_id, points in scores.items():
            if points == 3:
                players_result[player_id] = {"result": "WIN", "points": 3}
            elif points == 0 and winner_id:
                players_result[player_id] = {"result": "LOSS", "points": 0}
            else:
                players_result[player_id] = {"result": "TIE", "points": 1}

        # Report to league
        await client.call_tool(
            config.league_manager_endpoint,
            "report_match_result",
            {
                "match_id": match_id,
                "players": players_result
            }
        )

        logger.info("Result reported to league", match_id=match_id)

    except Exception as e:
        logger.error(
            "League reporting failed",
            match_id=match_id,
            error=str(e)
        )
    finally:
        await client.close()
