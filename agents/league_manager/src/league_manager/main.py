"""
League Manager - Main Entry Point.

FastAPI MCP server for tournament orchestration.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from .config import get_config
from .utils.logger import logger, setup_logger
from .storage.agent_registry import AgentRegistry
from .storage.league_store import LeagueStore
from .standings.calculator import StandingsCalculator
from .mcp_router import route_mcp_request


# Global instances
agent_registry: AgentRegistry = None
league_store: LeagueStore = None
standings_calc: StandingsCalculator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global agent_registry, league_store, standings_calc

    # Startup
    config = get_config()
    setup_logger("league_manager", config.log_dir)
    logger.info(
        "League Manager starting",
        port=config.port,
        league_id=config.league_id
    )

    # Initialize components
    agent_registry = AgentRegistry(config.data_dir, config.league_id)
    league_store = LeagueStore(config.data_dir, config.league_id)
    standings_calc = StandingsCalculator()

    # Load existing players into standings calculator
    existing_players = agent_registry.get_all_players()
    for player in existing_players:
        standings_calc.add_player(
            player["player_id"],
            player.get("display_name", player["player_id"])
        )

    if existing_players:
        logger.info(
            "Loaded existing players into standings",
            count=len(existing_players)
        )

    yield

    # Shutdown
    logger.info("League Manager shutting down")


# Create FastAPI app
app = FastAPI(
    title="League Manager",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """MCP JSON-RPC endpoint."""
    return await route_mcp_request(
        request,
        agent_registry,
        league_store,
        standings_calc
    )


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "league_manager"}


@app.post("/initialize")
async def initialize(request: dict):
    """
    MCP initialization handshake.
    Required by MCP protocol.
    """
    response_data = {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "even-odd-agent-league_manager",
                "version": "1.0.0"
            }
        },
        "id": request.get("id", 1)
    }
    return JSONResponse(content=response_data)


def main():
    """Main entry point."""
    config = get_config()

    uvicorn.run(
        app,
        host=config.host,
        port=config.port,
        reload=False
    )


if __name__ == "__main__":
    main()
