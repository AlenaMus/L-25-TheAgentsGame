"""
Match scheduler for tournament management.

Handles match ID generation, referee assignment, and round coordination.
"""

from typing import List, Dict
from league_manager.scheduler.round_robin import create_round_robin_schedule
from league_manager.utils.logger import logger


class Match:
    """
    Single match in the tournament.

    Attributes:
        match_id: Unique match identifier
        player_a_id: First player ID
        player_b_id: Second player ID
        referee_id: Assigned referee ID
        round_number: Round number (1-indexed)
    """

    def __init__(
        self,
        match_id: str,
        player_a_id: str,
        player_b_id: str,
        referee_id: str,
        round_number: int
    ):
        self.match_id = match_id
        self.player_a_id = player_a_id
        self.player_b_id = player_b_id
        self.referee_id = referee_id
        self.round_number = round_number

    def to_dict(self, league_id: str = None) -> dict:
        """Convert match to dictionary."""
        result = {
            "match_id": self.match_id,
            "player_A_id": self.player_a_id,
            "player_B_id": self.player_b_id,
            "referee_id": self.referee_id,
            "round_number": self.round_number,
            "status": "PENDING"
        }
        if league_id:
            result["league_id"] = league_id
        return result


class MatchScheduler:
    """
    Scheduler for match-referee assignments.

    Handles:
    - Match ID generation
    - Referee load balancing
    - Complete tournament scheduling
    """

    def __init__(self, league_id: str = "L1"):
        """Initialize scheduler."""
        self.league_id = league_id
        self.referee_workload: Dict[str, int] = {}

    def _generate_match_id(self, round_number: int, match_number: int) -> str:
        """
        Generate match ID.

        Format: {league_id}_R{round}_M{match}
        Example: "L1_R1_M001"
        """
        return f"{self.league_id}_R{round_number}_M{match_number:03d}"

    def _assign_referee(self, referees: List[dict]) -> str:
        """Assign least-loaded referee."""
        if not referees:
            raise ValueError("No referees available for assignment")

        # Find referee with minimum workload
        selected = min(
            referees,
            key=lambda r: self.referee_workload.get(r["referee_id"], 0)
        )
        referee_id = selected["referee_id"]

        # Increment workload
        self.referee_workload[referee_id] = \
            self.referee_workload.get(referee_id, 0) + 1

        return referee_id

    def create_tournament_schedule(
        self,
        player_ids: List[str],
        referees: List[dict]
    ) -> List[List[Match]]:
        """Create complete tournament schedule with referee assignments."""
        if len(player_ids) < 2:
            raise ValueError("Need at least 2 players for tournament")
        if not referees:
            raise ValueError("Need at least 1 referee for tournament")

        # Generate round-robin pairings
        rr_schedule = create_round_robin_schedule(player_ids)
        tournament_schedule: List[List[Match]] = []

        for round_idx, round_matches in enumerate(rr_schedule):
            round_number = round_idx + 1
            matches_in_round = [
                Match(
                    match_id=self._generate_match_id(round_number, idx + 1),
                    player_a_id=player_a,
                    player_b_id=player_b,
                    referee_id=self._assign_referee(referees),
                    round_number=round_number
                )
                for idx, (player_a, player_b) in enumerate(round_matches)
            ]
            tournament_schedule.append(matches_in_round)

        logger.info(
            "Tournament schedule created",
            total_rounds=len(tournament_schedule),
            total_matches=sum(len(r) for r in tournament_schedule)
        )

        return tournament_schedule


__all__ = ["Match", "MatchScheduler"]
