"""
Tournament Controller - Execute tournament flow and manage state transitions.

Controls the 7-stage tournament flow from registration to completion.
"""

import asyncio
from typing import Dict, Optional
from loguru import logger

from ..api.league_client import LeagueManagerClient
from .tournament_state import (
    TournamentState,
    TournamentStage,
    RegistrationStatus
)


class TournamentController:
    """Controls tournament execution and state transitions."""

    def __init__(
        self,
        league_manager_endpoint: str,
        auto_start: bool = True,
        registration_timeout: int = 120,
        min_players: int = 2,
        min_referees: int = 1
    ):
        """
        Initialize tournament controller.

        Args:
            league_manager_endpoint: League Manager MCP endpoint URL
            auto_start: Auto-start league after registrations complete
            registration_timeout: Max seconds to wait for registrations
            min_players: Minimum players required
            min_referees: Minimum referees required
        """
        self.client = LeagueManagerClient(league_manager_endpoint)
        self.auto_start = auto_start
        self.registration_timeout = registration_timeout

        # Initialize state
        self.state = TournamentState()
        self.state.registration.min_players = min_players
        self.state.registration.min_referees = min_referees

    async def wait_for_registrations(self) -> bool:
        """
        Wait for all agents to register (Stage 1-2).

        Returns:
            True if minimum registrations met
        """
        logger.info("Waiting for agent registrations...")
        self.state.advance_to_stage(
            TournamentStage.WAITING_REFEREE_REGISTRATION
        )

        start_time = asyncio.get_event_loop().time()

        while True:
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > self.registration_timeout:
                logger.error("Registration timeout reached")
                self.state.set_error("Registration timeout")
                return False

            # Poll registrations
            regs = await self.client.get_registrations()
            self.state.registration.referees_registered = len(
                regs.get("referees", [])
            )
            self.state.registration.players_registered = len(
                regs.get("players", [])
            )

            logger.info(
                "Registration progress",
                referees=self.state.registration.referees_registered,
                players=self.state.registration.players_registered
            )

            # Check if complete
            if self.state.registration.is_complete():
                logger.info("All registrations complete!")
                self.state.advance_to_stage(
                    TournamentStage.REGISTRATIONS_COMPLETE
                )
                return True

            # Wait before next poll
            await asyncio.sleep(2)

    async def start_tournament(self) -> bool:
        """
        Start the tournament (Stage 3).

        Returns:
            True if tournament started successfully
        """
        logger.info("Starting tournament...")
        self.state.advance_to_stage(TournamentStage.LEAGUE_STARTING)

        try:
            # Call League Manager to start league
            success = await self.client.start_league()

            if success:
                logger.info("League started successfully")
                self.state.advance_to_stage(TournamentStage.TOURNAMENT_RUNNING)

                # Get tournament info
                round_status = await self.client.get_round_status()
                self.state.total_rounds = round_status.get("total_rounds", 0)
                logger.info(f"Tournament has {self.state.total_rounds} rounds")

                return True
            else:
                logger.error("Failed to start league")
                self.state.set_error("League start failed")
                return False

        except Exception as e:
            logger.error("Error starting tournament", error=str(e))
            self.state.set_error(f"Tournament start error: {e}")
            return False

    async def monitor_tournament(self) -> Dict:
        """
        Monitor tournament progress (Stage 4-6).

        Returns:
            Current tournament status
        """
        try:
            # Get current round status
            round_status = await self.client.get_round_status()
            current_round = round_status.get("current_round", 0)

            # Update state if round changed
            if current_round > self.state.current_round:
                total_matches = round_status.get("total_matches", 0)
                self.state.start_round(current_round, total_matches)
                logger.info(
                    f"Round {current_round} started",
                    total_matches=total_matches
                )

            # Update round progress
            if current_round > 0:
                completed = round_status.get("completed_matches", 0)
                self.state.update_round_progress(current_round, completed)

            # Get standings
            standings = await self.client.get_standings()
            self.state.update_standings(standings)

            # Check if tournament is complete
            if self.state.is_tournament_complete():
                logger.info("Tournament completed!")
                self.state.advance_to_stage(TournamentStage.TOURNAMENT_COMPLETED)

            return self.state.get_summary()

        except Exception as e:
            logger.error("Error monitoring tournament", error=str(e))
            return {}

    async def pause_tournament(self) -> bool:
        """
        Pause tournament execution.

        Returns:
            True if paused successfully
        """
        logger.warning("Pausing tournament")
        self.state.advance_to_stage(TournamentStage.TOURNAMENT_PAUSED)
        return True

    async def resume_tournament(self) -> bool:
        """
        Resume paused tournament.

        Returns:
            True if resumed successfully
        """
        if self.state.stage != TournamentStage.TOURNAMENT_PAUSED:
            logger.warning("Tournament not paused")
            return False

        logger.info("Resuming tournament")
        self.state.advance_to_stage(TournamentStage.TOURNAMENT_RUNNING)
        return True

    def get_current_state(self) -> TournamentState:
        """Get current tournament state."""
        return self.state
