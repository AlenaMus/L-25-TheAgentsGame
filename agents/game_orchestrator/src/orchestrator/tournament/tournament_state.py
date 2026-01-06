"""
Tournament State Management - Track tournament execution state.

Manages the complete tournament state machine from registration to completion.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field


class TournamentStage(Enum):
    """7-stage tournament execution flow."""
    IDLE = "IDLE"
    WAITING_REFEREE_REGISTRATION = "WAITING_REFEREE_REGISTRATION"
    WAITING_PLAYER_REGISTRATION = "WAITING_PLAYER_REGISTRATION"
    REGISTRATIONS_COMPLETE = "REGISTRATIONS_COMPLETE"
    LEAGUE_STARTING = "LEAGUE_STARTING"
    TOURNAMENT_RUNNING = "TOURNAMENT_RUNNING"
    TOURNAMENT_PAUSED = "TOURNAMENT_PAUSED"
    TOURNAMENT_COMPLETED = "TOURNAMENT_COMPLETED"
    ERROR = "ERROR"


class RoundStatus(Enum):
    """Round execution status."""
    PENDING = "PENDING"
    ANNOUNCED = "ANNOUNCED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


@dataclass
class RegistrationStatus:
    """Registration tracking."""
    referees_registered: int = 0
    players_registered: int = 0
    min_referees: int = 1
    min_players: int = 2

    def is_complete(self) -> bool:
        """Check if minimum registrations are met."""
        return (
            self.referees_registered >= self.min_referees and
            self.players_registered >= self.min_players
        )

    def get_status(self) -> str:
        """Get human-readable status."""
        return (
            f"Referees: {self.referees_registered}/{self.min_referees}, "
            f"Players: {self.players_registered}/{self.min_players}"
        )


@dataclass
class RoundState:
    """State of a single round."""
    round_id: int
    total_matches: int = 0
    completed_matches: int = 0
    status: RoundStatus = RoundStatus.PENDING

    def is_complete(self) -> bool:
        """Check if round is complete."""
        return self.completed_matches >= self.total_matches

    def get_progress(self) -> str:
        """Get progress string."""
        return f"{self.completed_matches}/{self.total_matches} matches"


@dataclass
class TournamentState:
    """Complete tournament execution state."""
    stage: TournamentStage = TournamentStage.IDLE
    registration: RegistrationStatus = field(default_factory=RegistrationStatus)
    current_round: int = 0
    total_rounds: int = 0
    rounds: Dict[int, RoundState] = field(default_factory=dict)
    standings: List[Dict] = field(default_factory=list)
    error_message: Optional[str] = None

    def advance_to_stage(self, stage: TournamentStage) -> None:
        """Advance to next stage."""
        self.stage = stage

    def start_round(self, round_id: int, total_matches: int) -> None:
        """Start a new round."""
        self.current_round = round_id
        self.rounds[round_id] = RoundState(
            round_id=round_id,
            total_matches=total_matches,
            status=RoundStatus.ANNOUNCED
        )

    def update_round_progress(
        self,
        round_id: int,
        completed_matches: int
    ) -> None:
        """Update round progress."""
        if round_id in self.rounds:
            self.rounds[round_id].completed_matches = completed_matches
            if self.rounds[round_id].is_complete():
                self.rounds[round_id].status = RoundStatus.COMPLETED

    def complete_round(self, round_id: int) -> None:
        """Mark round as completed."""
        if round_id in self.rounds:
            self.rounds[round_id].status = RoundStatus.COMPLETED

    def is_tournament_complete(self) -> bool:
        """Check if tournament is complete."""
        return (
            self.current_round >= self.total_rounds and
            self.current_round > 0 and
            all(r.is_complete() for r in self.rounds.values())
        )

    def update_standings(self, standings: List[Dict]) -> None:
        """Update current standings."""
        self.standings = standings

    def set_error(self, error: str) -> None:
        """Set error state."""
        self.stage = TournamentStage.ERROR
        self.error_message = error

    def get_summary(self) -> Dict:
        """Get tournament summary."""
        return {
            "stage": self.stage.value,
            "current_round": self.current_round,
            "total_rounds": self.total_rounds,
            "registration_status": self.registration.get_status(),
            "standings_count": len(self.standings),
            "is_complete": self.is_tournament_complete()
        }
