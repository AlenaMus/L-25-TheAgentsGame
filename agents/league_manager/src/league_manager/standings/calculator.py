"""
Standings calculator.

Tracks wins/losses/draws and calculates tournament standings.
"""

from typing import Dict, List


class StandingsCalculator:
    """Calculate and maintain tournament standings."""
    
    def __init__(self):
        """Initialize standings calculator."""
        self.players: Dict[str, Dict] = {}
    
    def add_player(self, player_id: str, display_name: str) -> None:
        """
        Add player to standings.
        
        Args:
            player_id: Player identifier
            display_name: Player display name
        """
        self.players[player_id] = {
            "player_id": player_id,
            "display_name": display_name,
            "played": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "points": 0
        }
    
    def record_win(self, player_id: str) -> None:
        """Record a win for player."""
        if player_id not in self.players:
            # Auto-add player if not in standings yet (defensive)
            self.add_player(player_id, player_id)
        self.players[player_id]["wins"] += 1
        self.players[player_id]["points"] += 3
        self.players[player_id]["played"] += 1

    def record_loss(self, player_id: str) -> None:
        """Record a loss for player."""
        if player_id not in self.players:
            # Auto-add player if not in standings yet (defensive)
            self.add_player(player_id, player_id)
        self.players[player_id]["losses"] += 1
        self.players[player_id]["played"] += 1

    def record_draw(self, player_id: str) -> None:
        """Record a draw for player."""
        if player_id not in self.players:
            # Auto-add player if not in standings yet (defensive)
            self.add_player(player_id, player_id)
        self.players[player_id]["draws"] += 1
        self.players[player_id]["points"] += 1
        self.players[player_id]["played"] += 1
    
    def get_standings(self) -> List[Dict]:
        """
        Get current standings sorted by rank.
        
        Returns:
            List of player standings sorted by points (desc)
            
        Example:
            >>> calc = StandingsCalculator()
            >>> calc.add_player("P01", "Player 1")
            >>> calc.record_win("P01")
            >>> standings = calc.get_standings()
            >>> standings[0]["rank"]
            1
        """
        standings = list(self.players.values())
        
        # Sort by points (desc), then player_id (asc) for tiebreaker
        standings.sort(key=lambda p: (-p["points"], p["player_id"]))
        
        # Assign ranks
        for i, player in enumerate(standings):
            player["rank"] = i + 1
        
        return standings
