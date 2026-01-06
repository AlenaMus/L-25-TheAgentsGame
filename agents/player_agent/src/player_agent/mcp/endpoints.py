"""
MCP Server endpoint handlers.

Provides initialization handshake and health check endpoints.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Callable

from player_agent.utils.logger import logger


class EndpointHandlers:
    """Handlers for MCP server endpoints."""

    def __init__(
        self,
        agent_id: str,
        port: int,
        tool_handlers: Dict[str, Callable]
    ):
        """
        Initialize endpoint handlers.

        Args:
            agent_id: Agent identifier
            port: Server port
            tool_handlers: Dictionary of registered tool handlers
        """
        self.agent_id = agent_id
        self.port = port
        self.tool_handlers = tool_handlers

    async def handle_initialize(self, request: Request) -> JSONResponse:
        """
        MCP protocol initialization handshake.

        Args:
            request: FastAPI request object

        Returns:
            JSONResponse: Initialization response
        """
        try:
            body = await request.json()
            request_id = body.get("id", 1)

            logger.info("MCP initialization requested")

            response = {
                "jsonrpc": "2.0",
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {}
                    },
                    "serverInfo": {
                        "name": f"even-odd-agent-{self.agent_id}",
                        "version": "1.0.0"
                    }
                },
                "id": request_id
            }

            return JSONResponse(content=response)

        except Exception as e:
            logger.error(f"Initialization error: {str(e)}")
            # Create simple error response
            return JSONResponse(
                content={
                    "jsonrpc": "2.0",
                    "error": {
                        "code": -32603,
                        "message": f"Initialization failed: {str(e)}"
                    },
                    "id": None
                },
                status_code=200
            )

    async def handle_health_check(self) -> Dict[str, Any]:
        """
        Health check endpoint.

        Returns:
            dict: Health status information
        """
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "port": self.port,
            "tools": list(self.tool_handlers.keys())
        }
