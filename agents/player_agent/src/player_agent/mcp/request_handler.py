"""
JSON-RPC 2.0 request handling for MCP Server.

Handles request parsing, validation, and routing to tool handlers.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from typing import Callable, Dict, Optional
import traceback

from player_agent.mcp.schemas import JSONRPCRequest, JSONRPCResponse
from player_agent.mcp.error_responses import ErrorResponseFactory
from player_agent.utils.logger import logger


class RequestHandler:
    """Handles JSON-RPC 2.0 request processing and routing."""

    def __init__(
        self,
        agent_id: str,
        tool_handlers: Dict[str, Callable]
    ):
        """
        Initialize request handler.

        Args:
            agent_id: Agent identifier
            tool_handlers: Dictionary mapping method names to handlers
        """
        self.agent_id = agent_id
        self.tool_handlers = tool_handlers

    async def handle_mcp_request(self, request: Request) -> JSONResponse:
        """
        Main JSON-RPC 2.0 endpoint handler.

        Args:
            request: FastAPI request object

        Returns:
            JSONResponse: JSON-RPC 2.0 response
        """
        request_id = None

        try:
            # Parse request body
            body = await request.json()
            request_id = body.get("id")

            # Validate JSON-RPC structure
            try:
                rpc_request = JSONRPCRequest(**body)
            except ValidationError as e:
                return ErrorResponseFactory.create_error_response(
                    -32600,
                    "Invalid Request",
                    request_id,
                    str(e)
                )

            # Log incoming request
            logger.info(
                "Received JSON-RPC request",
                method=rpc_request.method,
                request_id=request_id,
                conversation_id=rpc_request.params.get("conversation_id")
            )

            # Route to handler
            return await self._route_request(rpc_request)

        except Exception as e:
            logger.error(
                f"Parse error in MCP endpoint: {str(e)}",
                exc_info=True
            )
            return ErrorResponseFactory.create_error_response(
                -32700,
                "Parse error",
                request_id
            )

    async def _route_request(
        self,
        rpc_request: JSONRPCRequest
    ) -> JSONResponse:
        """Route JSON-RPC request to appropriate handler."""
        method = rpc_request.method
        params = rpc_request.params or {}
        request_id = rpc_request.id

        # Check if method exists
        if method not in self.tool_handlers:
            return ErrorResponseFactory.create_error_response(
                -32601,
                f"Method not found: {method}",
                request_id
            )

        try:
            # Execute handler
            handler = self.tool_handlers[method]
            result = await handler(params)

            # Create success response
            response = JSONRPCResponse(
                jsonrpc="2.0",
                result=result,
                id=request_id
            )

            logger.info(
                "Tool execution successful",
                method=method,
                request_id=request_id
            )

            return JSONResponse(
                content=response.dict(exclude_none=True)
            )

        except ValidationError as e:
            logger.error(
                f"Validation error in {method}: {str(e)}",
                method=method,
                request_id=request_id
            )
            return ErrorResponseFactory.create_error_response(
                -32602,
                f"Invalid params: {str(e)}",
                request_id
            )

        except Exception as e:
            logger.error(
                f"Internal error in {method}: {str(e)}",
                method=method,
                request_id=request_id,
                traceback=traceback.format_exc()
            )
            return ErrorResponseFactory.create_error_response(
                -32603,
                f"Internal error: {str(e)}",
                request_id
            )
