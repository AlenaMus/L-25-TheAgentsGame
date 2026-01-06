"""
Game orchestrator - manages complete match lifecycle.

Implements the 6-phase game flow:
1. Send invitations
2. Collect choices (simultaneous)
3. Draw number
4. Evaluate winner
5. Notify players
6. Report to league manager
"""

from typing import Dict
from .game_logic import GameState, GameStateMachine
from .mcp_client import MCPClient
from .utils import logger
from .orchestration import (
    send_invitations,
    collect_choices,
    draw_and_evaluate,
    notify_players,
    report_result,
    report_aborted_game
)


async def orchestrate_game(match_params: Dict) -> None:
    """
    Orchestrate complete game from invitation to result reporting.

    Args:
        match_params: Match parameters containing:
            - match_id: Match identifier
            - round_id: Round identifier
            - player_A_id: Player A identifier
            - player_B_id: Player B identifier
            - player_A_endpoint: Player A HTTP endpoint
            - player_B_endpoint: Player B HTTP endpoint

    Example:
        >>> params = {
        ...     "match_id": "R1M1",
        ...     "round_id": "1",
        ...     "player_A_id": "P01",
        ...     "player_B_id": "P02",
        ...     "player_A_endpoint": "http://localhost:8101/mcp",
        ...     "player_B_endpoint": "http://localhost:8102/mcp"
        ... }
        >>> await orchestrate_game(params)
    """
    match_id = match_params["match_id"]
    logger.info("Starting game orchestration", match_id=match_id)

    # Create game state machine
    game = GameStateMachine(match_id)
    client = MCPClient()

    try:
        # Phase 1: Send invitations
        success = await send_invitations(client, match_params, game)
        if not success:
            return

        # Phase 2: Collect choices (simultaneous)
        choices = await collect_choices(client, match_params, game)
        if not choices:
            return

        # Phase 3: Draw and evaluate
        result = await draw_and_evaluate(match_params, game, choices)

        # Phase 4: Notify players
        await notify_players(client, match_params, result)

        # Phase 5: Report to league manager
        await report_result(client, match_params, result)

        logger.info("Game completed successfully", match_id=match_id)

    except Exception as e:
        logger.error(
            "Game orchestration failed",
            match_id=match_id,
            error=str(e),
            exc_info=True
        )
        game.transition(GameState.ABORTED)
        await report_aborted_game(client, match_params, str(e))
    finally:
        await client.close()
