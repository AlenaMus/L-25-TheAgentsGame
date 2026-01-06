"""
Agent registry for storing player information.

Caches player endpoints retrieved from League Manager.
"""

from typing import Dict, Optional
from pathlib import Path
import json


class AgentRegistry:
    """
    Local cache of player information.

    Stores player endpoints for quick lookup during match execution.
    """

    def __init__(self):
        """Initialize empty registry."""
        self.players: Dict[str, Dict] = {}

    def add_player(self, player_id: str, endpoint: str, display_name: str = "") -> None:
        """
        Add or update player in registry.

        Args:
            player_id: Player identifier
            endpoint: HTTP endpoint for MCP calls
            display_name: Human-readable name
        """
        self.players[player_id] = {
            "player_id": player_id,
            "endpoint": endpoint,
            "display_name": display_name
        }

    def get_player(self, player_id: str) -> Optional[Dict]:
        """
        Get player information.

        Args:
            player_id: Player identifier

        Returns:
            Player info or None if not found
        """
        return self.players.get(player_id)

    def update_from_league_data(self, players_data: list) -> None:
        """
        Update registry from League Manager data.

        Args:
            players_data: List of player dictionaries from League Manager
        """
        for player in players_data:
            self.add_player(
                player["player_id"],
                player["endpoint"],
                player.get("display_name", "")
            )
