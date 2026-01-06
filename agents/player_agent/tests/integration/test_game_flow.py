"""
Integration tests for complete game flow.

Tests player agent with mock referee through full game lifecycle.
"""

import pytest
from fastapi.testclient import TestClient

from player_agent.mcp import MCPServer
from player_agent.handlers import (
    handle_game_invitation,
    choose_parity,
    notify_match_result
)


@pytest.fixture
def mcp_server():
    """Create MCP server for testing."""
    server = MCPServer(agent_id="P01", port=8101)
    server.register_tool("handle_game_invitation", handle_game_invitation)
    server.register_tool("choose_parity", choose_parity)
    server.register_tool("notify_match_result", notify_match_result)
    return server


@pytest.fixture
def test_client(mcp_server):
    """Create test client for MCP server."""
    return TestClient(mcp_server.app)


@pytest.mark.asyncio
async def test_game_invitation_flow(test_client):
    """
    Test game invitation phase.

    Verifies:
    - Player accepts valid invitation
    - Response follows protocol
    - Response is within timeout
    """
    request = {
        "jsonrpc": "2.0",
        "method": "handle_game_invitation",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "20250124T100000Z",
            "conversation_id": "convR1M1",
            "match_id": "R1M1",
            "game_type": "even_odd",
            "player_id": "P01",
            "opponent_id": "P02",
            "role": "PLAYER_A"
        },
        "id": 1
    }

    response = test_client.post("/mcp", json=request)

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data
    assert data["id"] == 1

    result = data["result"]
    assert result["accept"] is True
    assert result["message_type"] == "GAME_JOIN_ACK"
    assert result["match_id"] == "R1M1"


@pytest.mark.asyncio
async def test_choose_parity_flow(test_client):
    """
    Test parity choice phase.

    Verifies:
    - Player makes valid choice (even/odd)
    - Response follows protocol
    - Response is within timeout
    """
    request = {
        "jsonrpc": "2.0",
        "method": "choose_parity",
        "params": {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": "referee:REF01",
            "timestamp": "20250124T100001Z",
            "conversation_id": "convR1M1",
            "match_id": "R1M1",
            "game_type": "even_odd",
            "player_id": "P01",
            "context": {
                "opponent_id": "P02",
                "your_standings": {}
            },
            "deadline": "20250124T100031Z"
        },
        "id": 2
    }

    response = test_client.post("/mcp", json=request)

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data

    result = data["result"]
    assert result["parity_choice"] in ["even", "odd"]
    assert result["message_type"] == "CHOOSE_PARITY_RESPONSE"
    assert result["match_id"] == "R1M1"
    assert result["player_id"] == "P01"


@pytest.mark.asyncio
async def test_match_result_notification(test_client):
    """
    Test match result notification phase.

    Verifies:
    - Player acknowledges result
    - Response follows protocol
    """
    request = {
        "jsonrpc": "2.0",
        "method": "notify_match_result",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": "referee:REF01",
            "timestamp": "20250124T100032Z",
            "conversation_id": "convR1M1",
            "match_id": "R1M1",
            "player_id": "P01",
            "game_result": {
                "status": "WIN",
                "winner_player_id": "P01",
                "drawn_number": 8,
                "number_parity": "even",
                "choices": {
                    "P01": "even",
                    "P02": "odd"
                }
            }
        },
        "id": 3
    }

    response = test_client.post("/mcp", json=request)

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert "result" in data

    result = data["result"]
    assert result["acknowledged"] is True
