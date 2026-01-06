"""
Round management and state coordination.

Handles round creation, announcements, match completion tracking,
and automatic round progression.
"""

from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime, timezone
from league_manager.scheduler import Match
from league_manager.standings import StandingsCalculator
from league_manager.broadcast import Broadcaster, MessageBuilder
from league_manager.utils.logger import logger


class RoundStatus(Enum):
    """Round state enumeration."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class RoundManager:
    """Manages tournament rounds and match progression."""

    def __init__(self, standings_calculator: StandingsCalculator,
                 broadcaster: Broadcaster,
                 message_builder: MessageBuilder,
                 agent_store,
                 league_id: str = "league_2025_even_odd"):
        """Initialize round manager."""
        self.standings_calculator = standings_calculator
        self.broadcaster = broadcaster
        self.message_builder = message_builder
        self.agent_store = agent_store
        self.league_id = league_id
        self.current_round: Optional[int] = None
        self.round_status: Dict[int, RoundStatus] = {}
        self.round_matches: Dict[int, List[Match]] = {}
        self.completed_matches: Dict[int, set] = {}
        self.total_rounds: int = 0

    def initialize_tournament(self, tournament_schedule: List[List[Match]]) -> None:
        """Initialize tournament with complete schedule."""
        self.total_rounds = len(tournament_schedule)
        self.current_round = None

        for round_idx, matches in enumerate(tournament_schedule):
            round_number = round_idx + 1
            self.round_matches[round_number] = matches
            self.round_status[round_number] = RoundStatus.PENDING
            self.completed_matches[round_number] = set()

        logger.info("Tournament initialized", total_rounds=self.total_rounds,
                   total_matches=sum(len(m) for m in tournament_schedule))

    async def start_round(self, round_number: int) -> Dict:
        """Start a round and broadcast announcement to all players."""
        if round_number not in self.round_matches:
            raise ValueError(f"Round {round_number} does not exist")
        if self.round_status[round_number] != RoundStatus.PENDING:
            raise ValueError(
                f"Round {round_number} already {self.round_status[round_number].value}"
            )

        self.current_round = round_number
        self.round_status[round_number] = RoundStatus.IN_PROGRESS
        announcement = self._create_round_announcement(round_number)

        # Broadcast to all players
        players = self.agent_store.get_all_players()
        report = await self.broadcaster.broadcast_to_players(players, announcement)

        logger.info("Round started and announced", round_number=round_number,
                   matches=len(self.round_matches[round_number]),
                   delivered=f"{report.successful}/{report.total}")
        return announcement

    def _create_round_announcement(self, round_number: int) -> Dict:
        """Create ROUND_ANNOUNCEMENT message."""
        matches = self.round_matches[round_number]
        return {
            "protocol": "league.v2",
            "message_type": "ROUND_ANNOUNCEMENT",
            "sender": "league_manager",
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "conversation_id": f"conv_round_{round_number}_announcement",
            "league_id": self.league_id,
            "round_id": round_number,
            "matches": [
                {
                    "match_id": m.match_id,
                    "game_type": "even_odd",
                    "player_A_id": m.player_a_id,
                    "player_B_id": m.player_b_id,
                    "referee_endpoint": f"referee:{m.referee_id}"
                }
                for m in matches
            ]
        }

    def mark_match_complete(self, match_id: str, round_number: int) -> bool:
        """Mark match complete and check if round is done."""
        if round_number not in self.completed_matches:
            logger.warning("Invalid round for match completion",
                          match_id=match_id, round_number=round_number)
            return False

        self.completed_matches[round_number].add(match_id)
        total_matches = len(self.round_matches[round_number])
        completed = len(self.completed_matches[round_number])
        logger.debug("Match completed", match_id=match_id,
                    round_number=round_number,
                    completed=f"{completed}/{total_matches}")
        return completed == total_matches

    async def complete_round(self, round_number: int) -> Dict:
        """Complete round and broadcast completion to all players."""
        self.round_status[round_number] = RoundStatus.COMPLETED
        total_matches = len(self.round_matches[round_number])
        next_round = (round_number + 1 if round_number < self.total_rounds else None)

        # Build completion message using MessageBuilder
        message = self.message_builder.build_round_completed(
            round_id=round_number,
            matches_completed=total_matches,
            next_round_id=next_round
        )

        # Broadcast to all players
        players = self.agent_store.get_all_players()
        report = await self.broadcaster.broadcast_to_players(players, message)

        logger.info("Round completed and broadcast", round_number=round_number,
                   next_round=next_round,
                   delivered=f"{report.successful}/{report.total}")
        return message

    def get_current_round(self) -> Optional[int]:
        """Get current round number."""
        return self.current_round

    def is_tournament_complete(self) -> bool:
        """Check if all rounds are complete."""
        return all(s == RoundStatus.COMPLETED for s in self.round_status.values())

    async def broadcast_tournament_end(self) -> Dict:
        """Broadcast tournament end to all players."""
        standings = self.standings_calculator.get_standings()

        # Convert PlayerStanding objects to dictionaries
        standings_dicts = [
            {
                "player_id": s.player_id,
                "display_name": s.display_name,
                "rank": s.rank,
                "points": s.points,
                "wins": s.wins,
                "losses": s.losses,
                "ties": s.ties,
                "matches_played": s.matches_played
            }
            for s in standings
        ]

        champion = standings_dicts[0] if standings_dicts else None
        total_matches = sum(len(matches) for matches in self.round_matches.values())

        message = self.message_builder.build_tournament_end(
            total_rounds=self.total_rounds,
            total_matches=total_matches,
            champion=champion,
            final_standings=standings_dicts
        )

        # Broadcast to all players
        players = self.agent_store.get_all_players()
        report = await self.broadcaster.broadcast_to_players(players, message)

        logger.info("Tournament end broadcast",
                   champion=champion.get("player_id") if champion else None,
                   delivered=f"{report.successful}/{report.total}")
        return message


__all__ = ["RoundManager", "RoundStatus"]
