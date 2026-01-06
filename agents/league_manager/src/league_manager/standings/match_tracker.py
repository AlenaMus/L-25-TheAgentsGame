"""
Match result tracking and head-to-head record management.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class MatchResult:
    """Represents the outcome of a single match."""

    match_id: str
    player_a_id: str
    player_b_id: str
    winner_id: Optional[str]
    result_type: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MatchTracker:
    """
    Track match results and maintain head-to-head records.

    Records all match outcomes and provides methods to query player
    statistics and head-to-head records between specific players.
    """

    def __init__(self):
        """Initialize empty match tracking storage."""
        self.matches: List[MatchResult] = []
        self.head_to_head: Dict[Tuple[str, str], str] = {}
        self.player_stats: Dict[str, Dict[str, int]] = {}

    def record_match(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        winner_id: Optional[str],
        result_type: str = "WIN"
    ) -> None:
        """
        Record a match result and update statistics.

        Args:
            match_id: Unique match identifier
            player_a_id: First player ID
            player_b_id: Second player ID
            winner_id: Winner's player ID (None for tie)
            result_type: Type of result (WIN, TIE, TECHNICAL_LOSS)

        Raises:
            ValueError: If winner_id is not one of the players or None
        """
        if winner_id is not None and winner_id not in (player_a_id, player_b_id):
            raise ValueError(f"Winner {winner_id} not in match players")

        self.matches.append(MatchResult(
            match_id=match_id,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            winner_id=winner_id,
            result_type=result_type
        ))

        # Update head-to-head records
        if winner_id == player_a_id:
            self.head_to_head[(player_a_id, player_b_id)] = "W"
            self.head_to_head[(player_b_id, player_a_id)] = "L"
        elif winner_id == player_b_id:
            self.head_to_head[(player_a_id, player_b_id)] = "L"
            self.head_to_head[(player_b_id, player_a_id)] = "W"
        else:
            self.head_to_head[(player_a_id, player_b_id)] = "T"
            self.head_to_head[(player_b_id, player_a_id)] = "T"

        # Initialize player stats if needed
        for player_id in (player_a_id, player_b_id):
            if player_id not in self.player_stats:
                self.player_stats[player_id] = {
                    "wins": 0, "losses": 0, "ties": 0, "matches_played": 0
                }

        # Update player statistics
        if winner_id is None:
            self.player_stats[player_a_id]["ties"] += 1
            self.player_stats[player_a_id]["matches_played"] += 1
            self.player_stats[player_b_id]["ties"] += 1
            self.player_stats[player_b_id]["matches_played"] += 1
        else:
            loser_id = player_b_id if winner_id == player_a_id else player_a_id
            self.player_stats[winner_id]["wins"] += 1
            self.player_stats[winner_id]["matches_played"] += 1
            self.player_stats[loser_id]["losses"] += 1
            self.player_stats[loser_id]["matches_played"] += 1

    def get_head_to_head(self, player_id: str, opponent_id: str) -> Optional[str]:
        """
        Get head-to-head result between two players.

        Returns: "W" if player_id won, "L" if lost, "T" if tied, None if not played
        """
        return self.head_to_head.get((player_id, opponent_id))

    def get_player_stats(self, player_id: str) -> Dict[str, int]:
        """Get statistics for a specific player."""
        return self.player_stats.get(player_id, {
            "wins": 0, "losses": 0, "ties": 0, "matches_played": 0
        })

    def get_all_matches(self) -> List[MatchResult]:
        """Get all recorded match results."""
        return self.matches.copy()


__all__ = ["MatchTracker", "MatchResult"]
