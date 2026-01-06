"""
Unit tests for MCP Server.

Tests the FastAPI-based MCP server including:
- Tool registration
- JSON-RPC 2.0 request handling
- Error responses
- Initialization handshake
- Health checks
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from player_agent.mcp.server import MCPServer


@pytest.fixture
def mcp_server():
    """Create MCP server instance for testing."""
    return MCPServer(agent_id="P01", port=8101)


@pytest.fixture
def client(mcp_server):
    """Create test client for FastAPI app."""
    return TestClient(mcp_server.app)


def test_mcp_server_initialization(mcp_server):
    """
    Test that MCP server initializes correctly.

    Arrange: Create MCPServer instance
    Act: Check attributes
    Assert: All attributes set correctly
    """
    assert mcp_server.agent_id == "P01"
    assert mcp_server.port == 8101
    assert mcp_server.app is not None
    assert isinstance(mcp_server.tool_handlers, dict)


def test_mcp_server_tool_registration():
    """
    Test tool registration mechanism.

    Arrange: Create server and dummy handler
    Act: Register tool
    Assert: Tool appears in handlers dict
    """
    server = MCPServer("P01", 8101)

    async def dummy_handler(params):
        return {"result": "success"}

    server.register_tool("test_tool", dummy_handler)

    assert "test_tool" in server.tool_handlers
    assert server.tool_handlers["test_tool"] == dummy_handler


def test_mcp_server_multiple_tool_registration():
    """
    Test registering multiple tools.

    Arrange: Create server
    Act: Register three tools
    Assert: All tools registered
    """
    server = MCPServer("P01", 8101)

    async def tool1(params):
        return {}

    async def tool2(params):
        return {}

    async def tool3(params):
        return {}

    server.register_tool("tool1", tool1)
    server.register_tool("tool2", tool2)
    server.register_tool("tool3", tool3)

    assert len(server.tool_handlers) == 3
    assert "tool1" in server.tool_handlers
    assert "tool2" in server.tool_handlers
    assert "tool3" in server.tool_handlers


@pytest.mark.asyncio
async def test_health_endpoint(client):
    """
    Test health check endpoint.

    Arrange: Setup test client
    Act: GET /health
    Assert: Returns status and agent info
    """
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["agent_id"] == "P01"
    assert data["port"] == 8101
    assert "tools" in data


@pytest.mark.asyncio
async def test_initialize_endpoint(client):
    """
    Test MCP initialization handshake.

    Arrange: Setup test client
    Act: POST /initialize with JSON-RPC request
    Assert: Returns correct protocol version and capabilities
    """
    request_data = {
        "jsonrpc": "2.0",
        "method": "initialize",
        "params": {},
        "id": 1
    }

    response = client.post("/initialize", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["result"]["protocolVersion"] == "2024-11-05"
    assert "capabilities" in data["result"]
    assert data["id"] == 1


@pytest.mark.asyncio
async def test_mcp_endpoint_valid_request(mcp_server, client):
    """
    Test valid JSON-RPC request to MCP endpoint.

    Arrange: Register test tool
    Act: POST valid JSON-RPC request
    Assert: Returns success response
    """
    async def test_handler(params):
        return {"status": "ok"}

    mcp_server.register_tool("test_method", test_handler)

    request_data = {
        "jsonrpc": "2.0",
        "method": "test_method",
        "params": {"key": "value"},
        "id": 42
    }

    response = client.post("/mcp", json=request_data)

    assert response.status_code == 200
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert data["result"] == {"status": "ok"}
    assert data["id"] == 42


@pytest.mark.asyncio
async def test_mcp_endpoint_method_not_found(client):
    """
    Test error when method doesn't exist.

    Arrange: Setup client
    Act: POST request for non-existent method
    Assert: Returns -32601 error (Method not found)
    """
    request_data = {
        "jsonrpc": "2.0",
        "method": "nonexistent_method",
        "params": {},
        "id": 1
    }

    response = client.post("/mcp", json=request_data)

    assert response.status_code == 200  # JSON-RPC uses 200 for errors
    data = response.json()
    assert data["jsonrpc"] == "2.0"
    assert "error" in data
    assert data["error"]["code"] == -32601
    assert "not found" in data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_mcp_endpoint_invalid_json():
    """
    Test error when JSON is malformed.

    Arrange: Setup client
    Act: POST invalid JSON
    Assert: Returns -32700 error (Parse error)
    """
    server = MCPServer("P01", 8101)
    client = TestClient(server.app)

    response = client.post(
        "/mcp",
        data="invalid json{{{",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == -32700
