"""
MCP Client for calling tools on remote agents.

Handles JSON-RPC 2.0 communication with players and league manager.
"""

import httpx
from typing import Dict, Any
from .utils.logger import logger


class MCPClient:
    """
    Client for calling MCP tools on remote agents.

    Attributes:
        timeout: Default timeout for requests (seconds)
        client: Async HTTP client

    Example:
        >>> client = MCPClient(timeout=30)
        >>> result = await client.call_tool(
        ...     "http://localhost:8101/mcp",
        ...     "choose_parity",
        ...     {"match_id": "R1M1"}
        ... )
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize MCP client.

        Args:
            timeout: Default timeout for requests (seconds)
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def call_tool(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        request_id: int = 1
    ) -> Dict[str, Any]:
        """
        Call an MCP tool on a remote agent.

        Args:
            endpoint: HTTP endpoint (e.g., "http://localhost:8101/mcp")
            method: Tool name (e.g., "choose_parity")
            params: Tool parameters (message envelope)
            request_id: JSON-RPC request ID

        Returns:
            Response dictionary (result or error)

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If HTTP error occurs
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logger.error(
                "Timeout calling MCP tool",
                endpoint=endpoint,
                method=method
            )
            raise
        except httpx.HTTPError as e:
            logger.error(
                "HTTP error calling MCP tool",
                endpoint=endpoint,
                method=method,
                error=str(e)
            )
            raise

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()
