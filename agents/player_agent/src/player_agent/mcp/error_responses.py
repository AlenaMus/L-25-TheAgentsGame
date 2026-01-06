"""
JSON-RPC 2.0 error response creation.

Handles creation of standardized error responses.
"""

from fastapi.responses import JSONResponse
from typing import Optional

from player_agent.mcp.schemas import JSONRPCError, JSONRPCResponse


class ErrorResponseFactory:
    """Factory for creating JSON-RPC error responses."""

    @staticmethod
    def create_error_response(
        code: int,
        message: str,
        request_id: Optional[int],
        data: Optional[str] = None
    ) -> JSONResponse:
        """
        Create JSON-RPC error response.

        Args:
            code: Error code
            message: Error message
            request_id: Request ID
            data: Additional error data

        Returns:
            JSONResponse: Error response
        """
        error = JSONRPCError(code=code, message=message, data=data)
        response = JSONRPCResponse(
            jsonrpc="2.0",
            error=error,
            id=request_id
        )

        return JSONResponse(
            content=response.dict(exclude_none=True),
            status_code=200  # JSON-RPC errors use 200 status
        )
