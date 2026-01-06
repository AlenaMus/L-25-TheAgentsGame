"""
League Manager API Client - Interface for communicating with League Manager.

Provides typed methods for all League Manager queries and commands.
"""

import httpx
from typing import Dict, List, Optional
from loguru import logger


class LeagueManagerClient:
    """Client for League Manager JSON-RPC API."""

    def __init__(self, endpoint: str, timeout: float = 10.0):
        """
        Initialize League Manager client.

        Args:
            endpoint: League Manager MCP endpoint URL
            timeout: Request timeout in seconds
        """
        self.endpoint = endpoint
        self.timeout = timeout
        self._request_id = 1000

    def _next_id(self) -> int:
        """Get next request ID."""
        self._request_id += 1
        return self._request_id

    async def get_registrations(self) -> Dict[str, List[Dict]]:
        """
        Query registered players and referees.

        Returns:
            Dict with 'players' and 'referees' lists
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "league_query",
                        "params": {"query_type": "GET_REGISTRATIONS"},
                        "id": self._next_id()
                    }
                )

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    return {
                        "players": result.get("players", []),
                        "referees": result.get("referees", [])
                    }
                return {"players": [], "referees": []}

        except Exception as e:
            logger.error("Failed to get registrations", error=str(e))
            return {"players": [], "referees": []}

    async def start_league(self) -> bool:
        """
        Start the league (create schedule and announce first round).

        Returns:
            True if league started successfully
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "start_league",
                        "params": {},
                        "id": self._next_id()
                    }
                )

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    return result.get("success", False)
                return False

        except Exception as e:
            logger.error("Failed to start league", error=str(e))
            return False

    async def get_standings(self) -> List[Dict]:
        """
        Get current standings.

        Returns:
            List of player standings (sorted by rank)
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "league_query",
                        "params": {"query_type": "GET_STANDINGS"},
                        "id": self._next_id()
                    }
                )

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    return result.get("standings", [])
                return []

        except Exception as e:
            logger.error("Failed to get standings", error=str(e))
            return []

    async def get_round_status(self, round_id: Optional[int] = None) -> Dict:
        """
        Get round status information.

        Args:
            round_id: Round ID (None for current round)

        Returns:
            Dict with round status
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"query_type": "GET_ROUND_STATUS"}
                if round_id is not None:
                    params["round_id"] = round_id

                response = await client.post(
                    self.endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "league_query",
                        "params": params,
                        "id": self._next_id()
                    }
                )

                if response.status_code == 200:
                    return response.json().get("result", {})
                return {}

        except Exception as e:
            logger.error("Failed to get round status", error=str(e))
            return {}

    async def get_matches(self, round_id: Optional[int] = None) -> List[Dict]:
        """
        Get match results.

        Args:
            round_id: Round ID (None for all matches)

        Returns:
            List of match results
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                params = {"query_type": "GET_MATCHES"}
                if round_id is not None:
                    params["round_id"] = round_id

                response = await client.post(
                    self.endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "league_query",
                        "params": params,
                        "id": self._next_id()
                    }
                )

                if response.status_code == 200:
                    result = response.json().get("result", {})
                    return result.get("matches", [])
                return []

        except Exception as e:
            logger.error("Failed to get matches", error=str(e))
            return []
