"""
Referee MCP server implementation.

FastAPI-based MCP server for handling JSON-RPC 2.0 requests.
"""

from fastapi import FastAPI, Request
from typing import Dict, Any, Callable
from .config import config
from .utils import logger
from .handlers import handle_match_assignment


class RefereeServer:
    """
    MCP server for referee agent.

    Attributes:
        app: FastAPI application
        tool_handlers: Registered MCP tool handlers
    """

    def __init__(self):
        """Initialize referee MCP server."""
        self.app = FastAPI(title=f"Referee MCP Server - {config.referee_id}")
        self.tool_handlers: Dict[str, Callable] = {}

        # Setup routes
        self.app.post("/mcp")(self.mcp_endpoint)
        self.app.get("/health")(self.health_check)
        self.app.post("/initialize")(self.initialize)

        # Register tools
        self.register_tool("assign_match", handle_match_assignment)

    def register_tool(self, method_name: str, handler: Callable):
        """
        Register MCP tool handler.

        Args:
            method_name: Tool name
            handler: Async function to handle tool calls
        """
        self.tool_handlers[method_name] = handler
        logger.info("Tool registered", tool=method_name)

    async def mcp_endpoint(self, request: Request):
        """
        Main JSON-RPC 2.0 endpoint.

        All MCP tool calls route through this endpoint.

        Args:
            request: HTTP request

        Returns:
            JSON-RPC 2.0 response
        """
        try:
            body = await request.json()
        except Exception as e:
            return self._jsonrpc_error(
                -32700,
                "Parse error",
                request_id=None
            )

        # Validate JSON-RPC 2.0 structure
        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if jsonrpc != "2.0":
            return self._jsonrpc_error(
                -32600,
                "Invalid Request",
                request_id
            )

        if not method:
            return self._jsonrpc_error(
                -32600,
                "Missing method",
                request_id
            )

        # Route to handler
        if method not in self.tool_handlers:
            return self._jsonrpc_error(
                -32601,
                f"Method not found: {method}",
                request_id
            )

        try:
            result = await self.tool_handlers[method](params)
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        except Exception as e:
            logger.error(
                "Tool execution error",
                method=method,
                error=str(e),
                exc_info=True
            )
            return self._jsonrpc_error(
                -32603,
                f"Internal error: {str(e)}",
                request_id
            )

    async def health_check(self):
        """
        Health check endpoint.

        Returns:
            dict: Health status
        """
        return {
            "status": "healthy",
            "referee_id": config.referee_id,
            "port": config.referee_port,
            "tools": list(self.tool_handlers.keys())
        }

    async def initialize(self, request: Request):
        """
        MCP initialization handshake.

        Required by MCP protocol specification.

        Args:
            request: HTTP request

        Returns:
            MCP initialization response
        """
        body = await request.json()
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": f"even-odd-referee-{config.referee_id}",
                    "version": "1.0.0"
                }
            },
            "id": body.get("id", 1)
        }

    def _jsonrpc_error(
        self,
        code: int,
        message: str,
        request_id: Any
    ) -> Dict:
        """
        Create JSON-RPC 2.0 error response.

        Args:
            code: Error code
            message: Error message
            request_id: Request ID (or None)

        Returns:
            JSON-RPC error response
        """
        return {
            "jsonrpc": "2.0",
            "error": {"code": code, "message": message},
            "id": request_id
        }
