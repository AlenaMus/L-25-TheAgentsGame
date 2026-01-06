"""
Agent storage and token management.

In-memory storage for registered players and referees with their tokens.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone


class AgentStore:
    """
    In-memory storage for registered agents and tokens.

    Attributes:
        players: Dictionary mapping player_id to player metadata
        referees: Dictionary mapping referee_id to referee metadata
        player_tokens: Dictionary mapping player_id to auth_token
        referee_tokens: Dictionary mapping referee_id to auth_token

    Example:
        >>> store = AgentStore()
        >>> store.add_player("P01", "Alice", "http://localhost:9001/mcp", "tok_p01_xyz")
        >>> store.get_player("P01")
        {'player_id': 'P01', 'display_name': 'Alice', ...}
    """

    def __init__(self):
        """Initialize empty agent storage."""
        self.players: Dict[str, dict] = {}
        self.referees: Dict[str, dict] = {}
        self.player_tokens: Dict[str, str] = {}
        self.referee_tokens: Dict[str, str] = {}

    def add_player(
        self,
        player_id: str,
        display_name: str,
        endpoint: str,
        auth_token: str,
        game_types: List[str] = None,
        version: str = "1.0.0"
    ) -> dict:
        """
        Add a player to the registry.

        Args:
            player_id: Unique player ID (e.g., "P01")
            display_name: Human-readable name
            endpoint: MCP endpoint URL
            auth_token: Authentication token
            game_types: List of supported game types
            version: Agent version

        Returns:
            Player metadata dictionary
        """
        player_data = {
            "player_id": player_id,
            "display_name": display_name,
            "endpoint": endpoint,
            "game_types": game_types or ["even_odd"],
            "version": version,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        self.players[player_id] = player_data
        self.player_tokens[player_id] = auth_token
        return player_data

    def add_referee(
        self,
        referee_id: str,
        display_name: str,
        endpoint: str,
        auth_token: str,
        max_concurrent_matches: int = 2,
        game_types: List[str] = None,
        version: str = "1.0.0"
    ) -> dict:
        """
        Add a referee to the registry.

        Args:
            referee_id: Unique referee ID (e.g., "REF01")
            display_name: Human-readable name
            endpoint: MCP endpoint URL
            auth_token: Authentication token
            max_concurrent_matches: Maximum concurrent matches
            game_types: List of supported game types
            version: Agent version

        Returns:
            Referee metadata dictionary
        """
        referee_data = {
            "referee_id": referee_id,
            "display_name": display_name,
            "endpoint": endpoint,
            "max_concurrent_matches": max_concurrent_matches,
            "game_types": game_types or ["even_odd"],
            "version": version,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        self.referees[referee_id] = referee_data
        self.referee_tokens[referee_id] = auth_token
        return referee_data

    def get_player(self, player_id: str) -> Optional[dict]:
        """Get player metadata by ID."""
        return self.players.get(player_id)

    def get_referee(self, referee_id: str) -> Optional[dict]:
        """Get referee metadata by ID."""
        return self.referees.get(referee_id)

    def get_all_players(self) -> List[dict]:
        """Get all registered players."""
        return list(self.players.values())

    def get_all_referees(self) -> List[dict]:
        """Get all registered referees."""
        return list(self.referees.values())

    def validate_player_token(self, player_id: str, token: str) -> bool:
        """Validate a player's authentication token."""
        return self.player_tokens.get(player_id) == token

    def validate_referee_token(self, referee_id: str, token: str) -> bool:
        """Validate a referee's authentication token."""
        return self.referee_tokens.get(referee_id) == token

    def get_player_count(self) -> int:
        """Get total number of registered players."""
        return len(self.players)

    def get_referee_count(self) -> int:
        """Get total number of registered referees."""
        return len(self.referees)


__all__ = ["AgentStore"]
