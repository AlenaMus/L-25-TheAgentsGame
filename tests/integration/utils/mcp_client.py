"""
MCP Client - HTTP client for JSON-RPC 2.0 communication.

Provides async methods for calling MCP tools on remote agents.
"""

import httpx
from typing import Dict, Any, Optional
import uuid


class MCPClient:
    """
    HTTP client for MCP/JSON-RPC 2.0 communication.

    Simplifies making tool calls to remote agents.
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize MCP client.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def call_tool(
        self,
        endpoint: str,
        tool_name: str,
        params: Dict[str, Any],
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Call an MCP tool on a remote agent.

        Args:
            endpoint: Agent's HTTP endpoint (e.g., http://localhost:8000/mcp)
            tool_name: Name of the MCP tool to call
            params: Parameters to pass to the tool
            request_id: Optional request ID (auto-generated if not provided)

        Returns:
            dict: JSON-RPC response

        Raises:
            httpx.HTTPError: If request fails
        """
        if request_id is None:
            request_id = str(uuid.uuid4())

        # Direct method call - agents register tools as JSON-RPC methods
        payload = {
            "jsonrpc": "2.0",
            "method": tool_name,
            "params": params,
            "id": request_id
        }

        response = await self.client.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    async def list_tools(self, endpoint: str) -> Dict[str, Any]:
        """
        List available tools on a remote agent.

        Args:
            endpoint: Agent's HTTP endpoint

        Returns:
            dict: List of available tools
        """
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "id": str(uuid.uuid4())
        }

        response = await self.client.post(
            endpoint,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    async def health_check(self, endpoint: str) -> bool:
        """
        Check if an agent is healthy and responsive.

        Args:
            endpoint: Agent's HTTP endpoint

        Returns:
            bool: True if agent is healthy
        """
        try:
            # Try to list tools as a health check
            await self.list_tools(endpoint)
            return True
        except Exception:
            return False

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
