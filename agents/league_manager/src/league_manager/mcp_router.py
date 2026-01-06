"""
MCP request routing for League Manager.

Routes JSON-RPC method calls to appropriate handlers.
"""

from fastapi.responses import JSONResponse
from .utils.logger import logger
from .storage.agent_registry import AgentRegistry
from .storage.league_store import LeagueStore
from .standings.calculator import StandingsCalculator
from .handlers import (
    register_player,
    register_referee,
    report_match_result,
    get_standings,
    start_league,
    get_assigned_matches
)


async def route_mcp_request(
    request: dict,
    agent_registry: AgentRegistry,
    league_store: LeagueStore,
    standings_calc: StandingsCalculator
) -> JSONResponse:
    """
    Route MCP JSON-RPC request to appropriate handler.

    Args:
        request: JSON-RPC request dictionary
        agent_registry: Agent registry instance
        league_store: League store instance
        standings_calc: Standings calculator instance

    Returns:
        JSONResponse with result or error
    """
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id", 1)

    logger.info(
        "MCP request received",
        method=method,
        params_keys=list(params.keys()) if params else []
    )

    try:
        result = await _execute_method(
            method,
            params,
            agent_registry,
            league_store,
            standings_calc
        )

        return JSONResponse({
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        })

    except Exception as e:
        logger.error(
            "Error handling request",
            method=method,
            error=str(e),
            exc_info=True
        )
        return JSONResponse({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": str(e)},
            "id": request_id
        }, status_code=500)


async def _execute_method(
    method: str,
    params: dict,
    agent_registry: AgentRegistry,
    league_store: LeagueStore,
    standings_calc: StandingsCalculator
):
    """Execute the specified method with given parameters."""
    if method == "tools/list":
        return _get_tools_list()
    elif method == "register_player":
        return await register_player(params, agent_registry, standings_calc)
    elif method == "register_referee":
        return await register_referee(params, agent_registry)
    elif method == "report_match_result":
        return await report_match_result(params, standings_calc, league_store)
    elif method == "get_standings":
        return await get_standings(standings_calc)
    elif method == "start_league":
        return await start_league(agent_registry, league_store)
    elif method == "get_assigned_matches":
        return await get_assigned_matches(params, league_store)
    elif method == "league_query":
        return await _handle_league_query(
            params, agent_registry, league_store, standings_calc
        )
    else:
        raise ValueError(f"Unknown method: {method}")


def _get_tools_list() -> dict:
    """Get list of available MCP tools."""
    return {"tools": [
        {"name": "register_player", "description": "Register a player"},
        {"name": "register_referee", "description": "Register a referee"},
        {"name": "report_match_result", "description": "Report match result"},
        {"name": "get_standings", "description": "Get current standings"},
        {"name": "start_league", "description": "Start the league"},
        {"name": "get_assigned_matches", "description": "Get matches assigned to referee"},
        {"name": "league_query", "description": "Query league data"}
    ]}


async def _handle_league_query(
    params: dict,
    agent_registry: AgentRegistry,
    league_store: LeagueStore,
    standings_calc: StandingsCalculator
):
    """Handle league query requests."""
    query_type = params.get("query_type")

    if query_type == "GET_REGISTRATIONS":
        return {
            "players": agent_registry.get_all_players(),
            "referees": agent_registry.get_all_referees()
        }
    elif query_type == "GET_STANDINGS":
        return await get_standings(standings_calc)
    elif query_type == "GET_ROUND_STATUS":
        schedule = league_store.load_schedule()
        return {
            "current_round": 0,
            "total_rounds": len(schedule) if schedule else 0,
            "status": "NOT_STARTED"
        }
    elif query_type == "GET_MATCHES":
        return {"matches": []}
    else:
        raise ValueError(f"Unknown query type: {query_type}")
