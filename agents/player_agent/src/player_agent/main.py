"""
Player Agent P01 - Main Entry Point.

This module initializes and starts the player agent.
"""

import asyncio
import httpx
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI

from player_agent.utils.logger import logger, setup_logger
from player_agent.config import Config
from player_agent.mcp import MCPServer
from player_agent.handlers import (
    handle_game_invitation,
    choose_parity,
    notify_match_result
)


async def register_to_league():
    """Register player with League Manager."""
    from player_agent.config import config

    logger.info("Registering with League Manager", url=config.league_manager_url)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            payload = {
                "jsonrpc": "2.0",
                "method": "register_player",
                "params": {
                    "protocol": "league.v2",
                    "message_type": "LEAGUE_REGISTER_REQUEST",
                    "player_meta": {
                        "display_name": config.agent_id or "P01",
                        "version": "1.0.0",
                        "game_types": ["even_odd"],
                        "contact_endpoint": f"http://localhost:{config.port}/mcp"
                    }
                },
                "id": 1
            }

            response = await client.post(config.league_manager_url, json=payload)
            response.raise_for_status()
            result = response.json()

            if result.get("status") == "ACCEPTED" or (
                isinstance(result.get("result"), dict) and
                result["result"].get("status") == "ACCEPTED"
            ):
                registration_data = result.get("result", result)
                logger.info(
                    "Registration successful",
                    player_id=registration_data.get("player_id"),
                    league_id=registration_data.get("league_id")
                )
            else:
                logger.error(
                    "Registration rejected",
                    response=result
                )
    except Exception as e:
        logger.error(
            "Registration failed",
            error=str(e),
            exc_info=True
        )


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Manage application lifecycle and registration."""
    # Startup: Wait for server to be ready, then register
    await asyncio.sleep(2)  # Give server time to fully start
    asyncio.create_task(register_to_league())
    yield
    # Shutdown: cleanup if needed


# Initialize MCP server at module level for uvicorn
from player_agent.config import config

server = MCPServer(
    agent_id=config.agent_id or "P01",
    port=config.port
)

# Register MCP tools
server.register_tool("handle_game_invitation", handle_game_invitation)
server.register_tool("choose_parity", choose_parity)
server.register_tool("notify_match_result", notify_match_result)

# Add lifespan to trigger registration after startup
server.app.router.lifespan_context = lifespan

# Export app for uvicorn
app = server.app


def main():
    """Main entry point for Player Agent."""
    # Setup logging
    setup_logger(
        agent_id=config.agent_id or "P01",
        log_dir="SHARED/logs/agents"
    )

    logger.info(
        "Player Agent starting",
        version="1.0.0",
        port=config.port,
        agent_id=config.agent_id
    )

    logger.info(
        "Player Agent initialized successfully",
        tools=["handle_game_invitation", "choose_parity", "notify_match_result"]
    )

    # Start server (registration will happen automatically after startup)
    logger.info(f"Starting MCP server on port {config.port}")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.port,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse
    from player_agent.config import config

    parser = argparse.ArgumentParser(description="Player Agent")
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run the player agent server on"
    )
    args = parser.parse_args()

    # Override config port if provided
    if args.port:
        config.port = args.port

    main()
