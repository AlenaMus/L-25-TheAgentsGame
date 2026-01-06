"""
Standings calculation with tiebreaker logic.
Calculates tournament standings: points > head-to-head > alphabetical.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from .match_tracker import MatchTracker


@dataclass
class PlayerStanding:
    """Represents a player's standing in the league."""
    player_id: str
    display_name: str
    wins: int = 0
    losses: int = 0
    ties: int = 0
    points: int = 0
    matches_played: int = 0
    rank: int = 0


class StandingsCalculator:
    """
    Calculate and maintain tournament standings with tiebreakers.
    Scoring: Win=3, Tie=1, Loss=0. Tiebreakers: Points > H2H > Alpha.
    """

    def __init__(self, match_tracker: Optional[MatchTracker] = None):
        """Initialize standings calculator."""
        self.players: Dict[str, PlayerStanding] = {}
        self.match_tracker = match_tracker or MatchTracker()

    def add_player(self, player_id: str, display_name: str) -> PlayerStanding:
        """Initialize a player in standings."""
        standing = PlayerStanding(player_id=player_id, display_name=display_name)
        self.players[player_id] = standing
        return standing

    def record_match_result(
        self, match_id: str, player_a_id: str, player_b_id: str,
        winner_id: Optional[str]
    ) -> None:
        """Record match result and update standings."""
        if player_a_id not in self.players:
            raise KeyError(f"Player {player_a_id} not in standings")
        if player_b_id not in self.players:
            raise KeyError(f"Player {player_b_id} not in standings")

        self.match_tracker.record_match(match_id, player_a_id, player_b_id, winner_id)

        player_a = self.players[player_a_id]
        player_b = self.players[player_b_id]

        player_a.matches_played += 1
        player_b.matches_played += 1

        if winner_id is None:
            player_a.ties += 1
            player_a.points += 1
            player_b.ties += 1
            player_b.points += 1
        elif winner_id == player_a_id:
            player_a.wins += 1
            player_a.points += 3
            player_b.losses += 1
        else:
            player_b.wins += 1
            player_b.points += 3
            player_a.losses += 1

    def get_standings(self) -> List[PlayerStanding]:
        """
        Get current standings sorted by rank.
        Tiebreakers: 1) Points 2) Head-to-head 3) Alphabetical
        """
        standings = list(self.players.values())

        # Pre-calculate tiebreaker values
        tiebreaker_values = {
            p.player_id: self._get_tiebreaker_value(p, standings)
            for p in standings
        }

        # Sort with tiebreaker logic
        standings.sort(key=lambda p: (
            -p.points, tiebreaker_values[p.player_id], p.player_id
        ))

        # Assign ranks
        for i, player in enumerate(standings):
            player.rank = i + 1

        return standings

    def _get_tiebreaker_value(
        self, player: PlayerStanding, all_players: List[PlayerStanding]
    ) -> int:
        """Calculate tiebreaker value. Returns 0 if won H2H, 1 if lost."""
        tied_players = [
            p for p in all_players
            if p.points == player.points and p.player_id != player.player_id
        ]

        # Only apply head-to-head if exactly 2 players tied
        if len(tied_players) != 1:
            return 0

        opponent = tied_players[0]
        h2h = self.match_tracker.get_head_to_head(player.player_id, opponent.player_id)
        return 0 if h2h == "W" else (1 if h2h == "L" else 0)

    def get_player_standing(self, player_id: str) -> Optional[PlayerStanding]:
        """Get standing for a specific player."""
        return self.players.get(player_id)


__all__ = ["StandingsCalculator", "PlayerStanding"]
