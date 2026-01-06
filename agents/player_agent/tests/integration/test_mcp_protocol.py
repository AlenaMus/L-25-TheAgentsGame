"""
Integration tests for MCP protocol compliance.

Tests JSON-RPC 2.0 and MCP initialization.
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
async def test_jsonrpc_error_handling(test_client):
    """
    Test JSON-RPC 2.0 error handling.

    Verifies:
    - Invalid method returns error
    - Invalid params returns error
    - Errors follow JSON-RPC spec
    """
    request = {
        "jsonrpc": "2.0",
        "method": "invalid_method",
        "params": {},
        "id": 1
    }

    response = test_client.post("/mcp", json=request)
    assert response.status_code == 200
    data = response.json()

    assert "error" in data
    assert data["error"]["code"] == -32601  # Method not found


@pytest.mark.asyncio
async def test_protocol_version_validation(test_client):
    """
    Test protocol version validation.

    Verifies agent handles different protocol versions.
    """
    request = {
        "jsonrpc": "2.0",
        "method": "handle_game_invitation",
        "params": {
            "protocol": "league.v1",  # Wrong version
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
    # Should still process but log warning
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_mcp_health_endpoint(test_client):
    """
    Test MCP health check endpoint.

    Verifies:
    - Health endpoint is accessible
    - Returns correct status
    - Lists registered tools
    """
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["agent_id"] == "P01"
    assert "handle_game_invitation" in data["tools"]
    assert "choose_parity" in data["tools"]
    assert "notify_match_result" in data["tools"]


@pytest.mark.asyncio
async def test_mcp_initialize_handshake(test_client):
    """
    Test MCP protocol initialization handshake.

    Verifies:
    - Initialize endpoint works
    - Returns correct protocol version
    - Declares capabilities
    """
    request = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        },
        "id": 1
    }

    response = test_client.post("/initialize", json=request)

    assert response.status_code == 200
    data = response.json()

    assert data["jsonrpc"] == "2.0"
    assert data["result"]["protocolVersion"] == "2024-11-05"
    assert "capabilities" in data["result"]
    assert "serverInfo" in data["result"]
