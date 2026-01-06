"""
Result reporting and notification.

Notifies players and reports results to League Manager.
"""

import asyncio
from typing import Dict
from ..mcp_client import MCPClient
from ..config import config
from ..utils import logger, get_utc_timestamp


async def notify_players(
    client: MCPClient,
    match_params: Dict,
    result: Dict
) -> None:
    """
    Send GAME_OVER notification to both players.

    This is fire-and-forget - we don't wait for acknowledgment.

    Args:
        client: MCP client
        match_params: Match parameters
        result: Game result
    """
    match_id = match_params["match_id"]
    logger.info("Notifying players", match_id=match_id)

    game_over_params = {
        "protocol": "league.v2",
        "message_type": "GAME_OVER",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}001",
        "auth_token": config.auth_token or "",
        "match_id": match_id,
        "game_type": "even_odd",
        "game_result": result
    }

    # Send to both players (fire-and-forget)
    await asyncio.gather(
        client.call_tool(
            match_params["player_A_endpoint"],
            "notify_match_result",
            game_over_params
        ),
        client.call_tool(
            match_params["player_B_endpoint"],
            "notify_match_result",
            game_over_params
        ),
        return_exceptions=True
    )


async def report_result(
    client: MCPClient,
    match_params: Dict,
    result: Dict
) -> None:
    """
    Report match result to League Manager.

    Args:
        client: MCP client
        match_params: Match parameters
        result: Game result
    """
    match_id = match_params["match_id"]
    logger.info("Reporting result to league", match_id=match_id)

    report_params = {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_REPORT",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}report",
        "auth_token": config.auth_token or "",
        "league_id": config.league_id or "",
        "round_id": match_params["round_id"],
        "match_id": match_id,
        "game_type": "even_odd",
        "result": {
            "winner": result["winner_player_id"],
            "score": result["scores"],
            "details": {
                "drawn_number": result["drawn_number"],
                "choices": result["choices"]
            }
        }
    }

    await client.call_tool(
        config.league_manager_endpoint,
        "report_match_result",
        report_params
    )


async def report_aborted_game(
    client: MCPClient,
    match_params: Dict,
    reason: str
) -> None:
    """
    Report aborted game to League Manager.

    Args:
        client: MCP client
        match_params: Match parameters
        reason: Abort reason
    """
    match_id = match_params["match_id"]
    logger.warning(
        "Reporting aborted game",
        match_id=match_id,
        reason=reason
    )

    report_params = {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_REPORT",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}abort",
        "auth_token": config.auth_token or "",
        "league_id": config.league_id or "",
        "round_id": match_params["round_id"],
        "match_id": match_id,
        "game_type": "even_odd",
        "result": {
            "status": "ABORTED",
            "reason": reason
        }
    }

    try:
        await client.call_tool(
            config.league_manager_endpoint,
            "report_match_result",
            report_params
        )
    except Exception as e:
        logger.error(
            "Failed to report aborted game",
            match_id=match_id,
            error=str(e)
        )
