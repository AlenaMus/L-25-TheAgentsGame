"""
Integration tests for timeout handling (Task 7).

Tests that player agent properly handles timeout scenarios.
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
import httpx

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
async def test_invitation_responds_within_timeout(test_client):
    """
    Test that invitation response completes well within 5-second timeout.

    Expected:
        - Response received in < 1 second
        - Player accepts invitation
        - Response follows protocol
    """
    start_time = time.time()

    request = {
        "jsonrpc": "2.0",
        "method": "handle_game_invitation",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "20250124T100000Z",
            "conversation_id": "timeout_test_invite",
            "match_id": "TIMEOUT_M1",
            "game_type": "even_odd",
            "player_id": "P01",
            "opponent_id": "P02",
            "role": "PLAYER_A"
        },
        "id": 1
    }

    response = test_client.post("/mcp", json=request)
    elapsed = time.time() - start_time

    # Verify response is fast (< 1 second, well within 5s timeout)
    assert elapsed < 1.0, f"Invitation took {elapsed}s, should be < 1s"

    # Verify correct response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["accept"] is True


@pytest.mark.asyncio
async def test_choice_responds_within_timeout(test_client):
    """
    Test that parity choice completes well within 30-second timeout.

    Expected:
        - Response received in < 5 seconds
        - Valid choice returned
        - Response follows protocol
    """
    start_time = time.time()

    request = {
        "jsonrpc": "2.0",
        "method": "choose_parity",
        "params": {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": "referee:REF01",
            "timestamp": "20250124T100001Z",
            "conversation_id": "timeout_test_choice",
            "match_id": "TIMEOUT_M1",
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
    elapsed = time.time() - start_time

    # Verify response is fast (< 5 seconds, well within 30s timeout)
    assert elapsed < 5.0, f"Choice took {elapsed}s, should be < 5s"

    # Verify correct response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["parity_choice"] in ["even", "odd"]


@pytest.mark.asyncio
async def test_result_notification_no_timeout(test_client):
    """
    Test that result notification completes quickly.

    Expected:
        - Response received immediately (no timeout limit)
        - Player acknowledges result
        - Response follows protocol
    """
    start_time = time.time()

    request = {
        "jsonrpc": "2.0",
        "method": "notify_match_result",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": "referee:REF01",
            "timestamp": "20250124T100032Z",
            "conversation_id": "timeout_test_result",
            "match_id": "TIMEOUT_M1",
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
    elapsed = time.time() - start_time

    # Verify response is fast (< 1 second)
    assert elapsed < 1.0, f"Result notification took {elapsed}s"

    # Verify correct response
    assert response.status_code == 200
    data = response.json()
    assert data["result"]["acknowledged"] is True


@pytest.mark.asyncio
async def test_consecutive_operations_within_timeout(test_client):
    """
    Test full game flow completes within expected timeouts.

    Verifies:
        - Invitation: < 1s (well within 5s timeout)
        - Choice: < 5s (well within 30s timeout)
        - Result: < 1s (no timeout limit)
        - Total flow: < 10s
    """
    start_time = time.time()

    # Step 1: Invitation
    invite_req = {
        "jsonrpc": "2.0",
        "method": "handle_game_invitation",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": "referee:REF01",
            "timestamp": "20250124T100000Z",
            "conversation_id": "consecutive_test",
            "match_id": "CONSEC_M1",
            "game_type": "even_odd",
            "player_id": "P01",
            "opponent_id": "P02",
            "role": "PLAYER_A"
        },
        "id": 1
    }

    invite_resp = test_client.post("/mcp", json=invite_req)
    assert invite_resp.status_code == 200
    invite_time = time.time() - start_time
    assert invite_time < 1.0

    # Step 2: Choice
    choice_start = time.time()
    choice_req = {
        "jsonrpc": "2.0",
        "method": "choose_parity",
        "params": {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": "referee:REF01",
            "timestamp": "20250124T100001Z",
            "conversation_id": "consecutive_test",
            "match_id": "CONSEC_M1",
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

    choice_resp = test_client.post("/mcp", json=choice_req)
    assert choice_resp.status_code == 200
    choice_time = time.time() - choice_start
    assert choice_time < 5.0

    # Step 3: Result
    result_start = time.time()
    result_req = {
        "jsonrpc": "2.0",
        "method": "notify_match_result",
        "params": {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": "referee:REF01",
            "timestamp": "20250124T100032Z",
            "conversation_id": "consecutive_test",
            "match_id": "CONSEC_M1",
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

    result_resp = test_client.post("/mcp", json=result_req)
    assert result_resp.status_code == 200
    result_time = time.time() - result_start
    assert result_time < 1.0

    # Verify total time
    total_time = time.time() - start_time
    assert total_time < 10.0


@pytest.mark.asyncio
async def test_multiple_rapid_requests_no_timeout(test_client):
    """
    Test multiple rapid requests complete without timeout.

    Verifies:
        - Concurrent requests handled properly
        - No requests timeout
        - All responses valid
    """
    requests = []

    for i in range(10):
        requests.append({
            "jsonrpc": "2.0",
            "method": "choose_parity",
            "params": {
                "protocol": "league.v2",
                "message_type": "CHOOSE_PARITY_CALL",
                "sender": "referee:REF01",
                "timestamp": "20250124T100001Z",
                "conversation_id": f"rapid_{i}",
                "match_id": f"RAPID_M{i}",
                "game_type": "even_odd",
                "player_id": "P01",
                "context": {
                    "opponent_id": "P02",
                    "your_standings": {}
                },
                "deadline": "20250124T100031Z"
            },
            "id": i
        })

    start_time = time.time()

    # Send all requests rapidly
    responses = []
    for req in requests:
        resp = test_client.post("/mcp", json=req)
        responses.append(resp)

    elapsed = time.time() - start_time

    # Verify all completed quickly
    assert elapsed < 5.0, f"10 requests took {elapsed}s"

    # Verify all responses valid
    for resp in responses:
        assert resp.status_code == 200
        data = resp.json()
        assert data["result"]["parity_choice"] in ["even", "odd"]
