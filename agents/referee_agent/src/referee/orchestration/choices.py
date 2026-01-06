"""
Parity choice collection.

Collects choices from both players simultaneously (critical for fairness).
"""

import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional
from ..game_logic import GameState, GameStateMachine
from ..mcp_client import MCPClient
from ..config import config
from ..utils import logger, get_utc_timestamp


async def collect_choices(
    client: MCPClient,
    match_params: Dict,
    game: GameStateMachine
) -> Optional[Dict[str, str]]:
    """
    Collect parity choices from both players simultaneously.

    CRITICAL: Uses asyncio.gather() to ensure both calls happen
    at the same time, preventing timing-based advantage.

    Args:
        client: MCP client
        match_params: Match parameters
        game: Game state machine

    Returns:
        Dict mapping player_id to choice, or None if failed
    """
    match_id = match_params["match_id"]
    logger.info("Collecting choices", match_id=match_id)

    deadline = (
        datetime.now(timezone.utc) + timedelta(seconds=config.choice_timeout)
    ).strftime("%Y%m%dT%H%M%SZ")

    # Prepare choice requests
    choice_params_A = {
        "protocol": "league.v2",
        "message_type": "CHOOSE_PARITY_CALL",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}001",
        "auth_token": config.auth_token or "",
        "match_id": match_id,
        "game_type": "even_odd",
        "deadline": deadline,
        "player_id": match_params["player_A_id"],
        "context": {
            "opponent_id": match_params["player_B_id"],
            "round_id": match_params["round_id"]
        }
    }

    choice_params_B = {**choice_params_A}
    choice_params_B["player_id"] = match_params["player_B_id"]
    choice_params_B["context"]["opponent_id"] = match_params["player_A_id"]

    # Call both players SIMULTANEOUSLY (critical for fairness)
    try:
        results = await asyncio.gather(
            asyncio.wait_for(
                client.call_tool(
                    match_params["player_A_endpoint"],
                    "choose_parity",
                    choice_params_A
                ),
                timeout=config.choice_timeout
            ),
            asyncio.wait_for(
                client.call_tool(
                    match_params["player_B_endpoint"],
                    "choose_parity",
                    choice_params_B
                ),
                timeout=config.choice_timeout
            ),
            return_exceptions=True
        )

        # Extract and validate choices
        choices = {}
        for i, result in enumerate(results):
            player_id = (match_params["player_A_id"] if i == 0
                        else match_params["player_B_id"])

            if isinstance(result, Exception):
                logger.error(
                    "Player choice failed",
                    match_id=match_id,
                    player_id=player_id,
                    error=str(result)
                )
                game.transition(GameState.ABORTED)
                return None

            choice = result.get("result", {}).get("parity_choice")

            if choice not in ["even", "odd"]:
                logger.error(
                    "Invalid choice",
                    match_id=match_id,
                    player_id=player_id,
                    choice=choice
                )
                game.transition(GameState.ABORTED)
                return None

            choices[player_id] = choice

        game.transition(GameState.DRAWING_NUMBER)
        return choices

    except asyncio.TimeoutError:
        logger.error("Choice timeout", match_id=match_id)
        game.transition(GameState.ABORTED)
        return None
