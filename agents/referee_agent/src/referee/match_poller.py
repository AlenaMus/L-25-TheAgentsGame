"""
Match polling and execution coordinator.

Continuously polls League Manager for assigned matches and executes them.
"""

import asyncio
from .config import config
from .utils.logger import logger
from .mcp_client import MCPClient
from .match_executor import MatchExecutor
from .storage import AgentRegistry


async def match_polling_loop():
    """
    Poll League Manager for assigned matches and execute them.

    Runs continuously, checking for new matches every 5 seconds.
    """
    # Wait for registration to complete
    await asyncio.sleep(5)

    if not config.referee_id or not config.auth_token:
        logger.error("Cannot start match polling - not registered")
        return

    # Initialize components
    agent_registry = AgentRegistry()
    executor = MatchExecutor(agent_registry)
    processed_matches = set()

    logger.info("Match polling started", referee_id=config.referee_id)

    while True:
        try:
            client = MCPClient(timeout=10)
            try:
                # Fetch player list from League Manager
                players_response = await client.call_tool(
                    config.league_manager_endpoint,
                    "league_query",
                    {"query_type": "GET_REGISTRATIONS"}
                )
                players_result = players_response.get("result", {})
                players = players_result.get("players", [])
                agent_registry.update_from_league_data(players)

                # Get assigned matches
                matches_response = await client.call_tool(
                    config.league_manager_endpoint,
                    "get_assigned_matches",
                    {"referee_id": config.referee_id}
                )

                result = matches_response.get("result", {})
                matches = result.get("matches", [])

                # Execute pending matches
                for match in matches:
                    match_id = match["match_id"]
                    status = match.get("status", "PENDING")

                    if status == "PENDING" and match_id not in processed_matches:
                        logger.info("Executing match", match_id=match_id)
                        success = await executor.execute_match(match)
                        if success:
                            processed_matches.add(match_id)

            finally:
                await client.close()

        except Exception as e:
            logger.error("Match polling error", error=str(e), exc_info=True)

        # Poll every 5 seconds
        await asyncio.sleep(5)
