"""
Integration test for complete game lifecycle.

Tests full flow: Invitation -> Choice -> Result.
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
async def test_complete_game_lifecycle(test_client):
    """
    Test complete game flow from invitation to result.

    Verifies:
    - All phases complete successfully
    - Responses follow protocol throughout
    - Player maintains conversation_id
    """
    conversation_id = "convR1M1"
    match_id = "R1M1"

    # Phase 1: Invitation
    invitation_request = {
        "jsonrpc": "2.0",
        "method": "handle_game_invitation",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "20250124T100000Z",
            "conversation_id": conversation_id,
            "match_id": match_id,
            "game_type": "even_odd",
            "player_id": "P01",
            "opponent_id": "P02",
            "role": "PLAYER_A"
        },
        "id": 1
    }

    invitation_response = test_client.post("/mcp", json=invitation_request)
    assert invitation_response.status_code == 200
    invitation_data = invitation_response.json()
    assert invitation_data["result"]["accept"] is True
    assert invitation_data["result"]["conversation_id"] == conversation_id

    # Phase 2: Choice
    choice_request = {
        "jsonrpc": "2.0",
        "method": "choose_parity",
        "params": {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": "referee:REF01",
            "timestamp": "20250124T100001Z",
            "conversation_id": conversation_id,
            "match_id": match_id,
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

    choice_response = test_client.post("/mcp", json=choice_request)
    assert choice_response.status_code == 200
    choice_data = choice_response.json()
    player_choice = choice_data["result"]["parity_choice"]
    assert player_choice in ["even", "odd"]

    # Phase 3: Result
    result_request = {
        "jsonrpc": "2.0",
        "method": "notify_match_result",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": "referee:REF01",
            "timestamp": "20250124T100032Z",
            "conversation_id": conversation_id,
            "match_id": match_id,
            "player_id": "P01",
            "game_result": {
                "status": "WIN",
                "winner_player_id": "P01",
                "drawn_number": 8,
                "number_parity": "even",
                "choices": {
                    "P01": player_choice,
                    "P02": "odd" if player_choice == "even" else "even"
                }
            }
        },
        "id": 3
    }

    result_response = test_client.post("/mcp", json=result_request)
    assert result_response.status_code == 200
    result_data = result_response.json()
    assert result_data["result"]["acknowledged"] is True
