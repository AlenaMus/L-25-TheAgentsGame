"""
MCP Protocol Layer for Player Agent.

This package implements the Model Context Protocol (MCP) server
using JSON-RPC 2.0 over HTTP.
"""

from player_agent.mcp.server import MCPServer
from player_agent.mcp.schemas import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MessageEnvelope
)

__all__ = [
    "MCPServer",
    "JSONRPCRequest",
    "JSONRPCResponse",
    "JSONRPCError",
    "MessageEnvelope"
]
