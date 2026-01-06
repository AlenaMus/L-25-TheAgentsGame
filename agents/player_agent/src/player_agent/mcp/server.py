"""
FastAPI-based MCP Server implementation with JSON-RPC 2.0.

Provides HTTP endpoint for MCP protocol communication.
"""

from fastapi import FastAPI, Request
from typing import Callable, Dict

from player_agent.mcp.request_handler import RequestHandler
from player_agent.mcp.endpoints import EndpointHandlers
from player_agent.utils.logger import logger


class MCPServer:
    """
    MCP Server using FastAPI and JSON-RPC 2.0.

    Manages tool registration and request routing.

    Attributes:
        agent_id: Agent identifier
        port: Server port
        app: FastAPI application instance
        tool_handlers: Registered tool handlers

    Example:
        >>> server = MCPServer("P01", 8101)
        >>> server.register_tool("choose_parity", handler_func)
        >>> server.run()
    """

    def __init__(self, agent_id: str, port: int):
        """
        Initialize MCP server.

        Args:
            agent_id: Agent identifier (e.g., "P01")
            port: HTTP server port
        """
        self.agent_id = agent_id
        self.port = port
        self.app = FastAPI(
            title=f"Player Agent {agent_id}",
            description="MCP Server for Even/Odd Game League",
            version="1.0.0"
        )
        self.tool_handlers: Dict[str, Callable] = {}

        # Initialize handlers
        self.request_handler = RequestHandler(agent_id, self.tool_handlers)
        self.endpoint_handlers = EndpointHandlers(
            agent_id,
            port,
            self.tool_handlers
        )

        # Setup routes
        self.app.post("/mcp")(self._mcp_endpoint)
        self.app.post("/initialize")(self._initialize)
        self.app.get("/health")(self._health_check)

        logger.info(
            f"MCP Server initialized",
            agent_id=agent_id,
            port=port
        )

    def register_tool(self, method_name: str, handler: Callable):
        """
        Register an MCP tool handler.

        Args:
            method_name: Tool name (e.g., "choose_parity")
            handler: Async function to handle tool calls

        Example:
            >>> async def my_handler(params: dict) -> dict:
            ...     return {"result": "success"}
            >>> server.register_tool("my_tool", my_handler)
        """
        self.tool_handlers[method_name] = handler
        logger.info(f"Registered tool: {method_name}")

    async def _mcp_endpoint(self, request: Request):
        """Route to request handler."""
        return await self.request_handler.handle_mcp_request(request)

    async def _initialize(self, request: Request):
        """Route to initialization handler."""
        return await self.endpoint_handlers.handle_initialize(request)

    async def _health_check(self):
        """Route to health check handler."""
        return await self.endpoint_handlers.handle_health_check()
