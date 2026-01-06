"""
Protocol message builder for league broadcasts.

Constructs league.v2 protocol messages for various broadcast scenarios.
"""

from typing import Dict, List, Optional
from datetime import datetime, timezone


class MessageBuilder:
    """
    Build protocol-compliant messages for league broadcasts.

    All messages follow the league.v2 envelope format with proper
    timestamps and conversation IDs.

    Example:
        >>> builder = MessageBuilder(league_id="league_2025")
        >>> msg = builder.build_round_announcement(
        ...     round_id=1,
        ...     matches=[...]
        ... )
    """

    def __init__(self, league_id: str = "league_2025_even_odd"):
        """
        Initialize message builder.

        Args:
            league_id: League identifier
        """
        self.league_id = league_id

    def build_round_announcement(
        self,
        round_id: int,
        matches: List[Dict]
    ) -> Dict:
        """
        Build ROUND_ANNOUNCEMENT message.

        Args:
            round_id: Round number
            matches: List of match dictionaries with match_id, player_ids, etc.

        Returns:
            Protocol-compliant ROUND_ANNOUNCEMENT message
        """
        return {
            "protocol": "league.v2",
            "message_type": "ROUND_ANNOUNCEMENT",
            "sender": "league:league_manager",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"league_{self.league_id}_r{round_id}",
            "league_id": self.league_id,
            "round_id": round_id,
            "matches": matches
        }

    def build_round_completed(
        self,
        round_id: int,
        matches_completed: int,
        next_round_id: Optional[int] = None
    ) -> Dict:
        """
        Build ROUND_COMPLETED message.

        Args:
            round_id: Completed round number
            matches_completed: Number of matches completed
            next_round_id: Next round number (None if tournament complete)

        Returns:
            Protocol-compliant ROUND_COMPLETED message
        """
        return {
            "protocol": "league.v2",
            "message_type": "ROUND_COMPLETED",
            "sender": "league:league_manager",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"league_{self.league_id}_r{round_id}_complete",
            "league_id": self.league_id,
            "round_id": round_id,
            "matches_completed": matches_completed,
            "next_round_id": next_round_id
        }

    def build_tournament_start(
        self,
        total_rounds: int,
        total_matches: int,
        player_count: int
    ) -> Dict:
        """
        Build TOURNAMENT_START message.

        Args:
            total_rounds: Total number of rounds
            total_matches: Total number of matches
            player_count: Number of registered players

        Returns:
            Protocol-compliant TOURNAMENT_START message
        """
        return {
            "protocol": "league.v2",
            "message_type": "TOURNAMENT_START",
            "sender": "league:league_manager",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"league_{self.league_id}_start",
            "league_id": self.league_id,
            "total_rounds": total_rounds,
            "total_matches": total_matches,
            "player_count": player_count
        }

    def build_tournament_end(
        self,
        total_rounds: int,
        total_matches: int,
        champion: Dict,
        final_standings: List[Dict]
    ) -> Dict:
        """
        Build TOURNAMENT_END message.

        Args:
            total_rounds: Total rounds played
            total_matches: Total matches played
            champion: Champion player data
            final_standings: Complete final standings

        Returns:
            Protocol-compliant TOURNAMENT_END message
        """
        return {
            "protocol": "league.v2",
            "message_type": "TOURNAMENT_END",
            "sender": "league:league_manager",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"league_{self.league_id}_end",
            "league_id": self.league_id,
            "total_rounds": total_rounds,
            "total_matches": total_matches,
            "champion": champion,
            "final_standings": final_standings
        }

    def build_standings_update(
        self,
        round_id: int,
        standings: List[Dict]
    ) -> Dict:
        """
        Build LEAGUE_STANDINGS_UPDATE message.

        Args:
            round_id: Current round number
            standings: Current standings data

        Returns:
            Protocol-compliant LEAGUE_STANDINGS_UPDATE message
        """
        return {
            "protocol": "league.v2",
            "message_type": "LEAGUE_STANDINGS_UPDATE",
            "sender": "league:league_manager",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"league_{self.league_id}_r{round_id}_standings",
            "league_id": self.league_id,
            "round_id": round_id,
            "standings": standings
        }

    def _get_timestamp(self) -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


__all__ = ["MessageBuilder"]
