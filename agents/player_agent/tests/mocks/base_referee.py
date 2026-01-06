"""
Base referee functionality for mock testing.

Provides core JSON-RPC communication with player agent.
"""

import httpx
from typing import Dict, Any, Optional
from datetime import datetime, timezone


class BaseReferee:
    """
    Base referee with JSON-RPC communication.

    Handles low-level request/response with player agent.

    Attributes:
        player_url: Player agent endpoint URL
        referee_id: Referee identifier
        timeout: Default timeout for requests
        request_id: Request counter

    Example:
        >>> referee = BaseReferee("http://localhost:8101/mcp")
        >>> result = await referee.send_jsonrpc_request("method", {})
    """

    def __init__(
        self,
        player_url: str,
        referee_id: str = "REF01",
        timeout: float = 30.0
    ):
        """
        Initialize base referee.

        Args:
            player_url: Player agent MCP endpoint
            referee_id: Referee identifier
            timeout: Default request timeout
        """
        self.player_url = player_url
        self.referee_id = referee_id
        self.timeout = timeout
        self.request_id = 0

    def _next_request_id(self) -> int:
        """
        Generate next request ID.

        Returns:
            int: Incrementing request ID
        """
        self.request_id += 1
        return self.request_id

    def _get_timestamp(self) -> str:
        """
        Get current UTC timestamp.

        Returns:
            str: Timestamp in format YYYYMMDDTHHMMSSZ
        """
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    async def send_jsonrpc_request(
        self,
        method: str,
        params: Dict[str, Any],
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Send JSON-RPC 2.0 request to player agent.

        Args:
            method: Method name
            params: Method parameters
            timeout: Request timeout (optional)

        Returns:
            dict: Response result

        Raises:
            Exception: If request fails or times out
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self._next_request_id()
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.player_url,
                json=request,
                timeout=timeout or self.timeout
            )

            response.raise_for_status()
            data = response.json()

            # Check for JSON-RPC error
            if "error" in data:
                raise Exception(
                    f"JSON-RPC error: {data['error']['message']}"
                )

            return data.get("result", {})
