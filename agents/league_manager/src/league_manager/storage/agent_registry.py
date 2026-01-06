"""
Agent registry.

Stores and retrieves player and referee information.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional


class AgentRegistry:
    """Manages agent (player and referee) registration."""
    
    def __init__(self, data_dir: str = "SHARED/data", league_id: str = "league_2025_even_odd"):
        """
        Initialize agent registry.
        
        Args:
            data_dir: Base data directory
            league_id: League identifier
        """
        self.league_id = league_id
        self.base_dir = Path(data_dir) / "leagues" / league_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.players_file = self.base_dir / "players.json"
        self.referees_file = self.base_dir / "referees.json"
        
        # Load existing data
        self.players = self._load_json(self.players_file, {})
        self.referees = self._load_json(self.referees_file, {})
    
    def add_player(self, player_id: str, display_name: str, endpoint: str,
                   game_types: List[str], version: str, auth_token: str) -> None:
        """Add player to registry."""
        self.players[player_id] = {
            "player_id": player_id,
            "display_name": display_name,
            "endpoint": endpoint,
            "game_types": game_types,
            "version": version,
            "auth_token": auth_token
        }
        self._save_json(self.players_file, self.players)
    
    def add_referee(self, referee_id: str, display_name: str, endpoint: str,
                    game_types: List[str], max_concurrent: int, version: str,
                    auth_token: str) -> None:
        """Add referee to registry."""
        self.referees[referee_id] = {
            "referee_id": referee_id,
            "display_name": display_name,
            "endpoint": endpoint,
            "game_types": game_types,
            "max_concurrent": max_concurrent,
            "version": version,
            "auth_token": auth_token
        }
        self._save_json(self.referees_file, self.referees)
    
    def get_all_players(self) -> List[Dict]:
        """Get all registered players."""
        return list(self.players.values())
    
    def get_all_referees(self) -> List[Dict]:
        """Get all registered referees."""
        return list(self.referees.values())
    
    def player_count(self) -> int:
        """Get number of registered players."""
        return len(self.players)

    def find_player_by_endpoint(self, endpoint: str) -> Optional[Dict]:
        """
        Find player by endpoint.

        Args:
            endpoint: Player's contact endpoint

        Returns:
            Player dict if found, None otherwise
        """
        for player in self.players.values():
            if player.get("endpoint") == endpoint:
                return player
        return None

    def find_referee_by_endpoint(self, endpoint: str) -> Optional[Dict]:
        """
        Find referee by endpoint.

        Args:
            endpoint: Referee's contact endpoint

        Returns:
            Referee dict if found, None otherwise
        """
        for referee in self.referees.values():
            if referee.get("endpoint") == endpoint:
                return referee
        return None
    
    def referee_count(self) -> int:
        """Get number of registered referees."""
        return len(self.referees)
    
    def _load_json(self, file_path: Path, default: Dict) -> Dict:
        """Load JSON file or return default."""
        if file_path.exists():
            with open(file_path, 'r') as f:
                return json.load(f)
        return default
    
    def _save_json(self, file_path: Path, data: Dict) -> None:
        """Save data to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
