"""
Tournament monitoring and status broadcasting for Game Orchestrator.

Handles continuous monitoring of tournament progress and broadcasting updates.
"""

import asyncio
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import GameOrchestrator


class TournamentMonitor:
    """Monitors tournament execution and broadcasts updates."""

    def __init__(self, orchestrator: 'GameOrchestrator'):
        """
        Initialize tournament monitor.

        Args:
            orchestrator: Parent GameOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.tournament = orchestrator.tournament
        self.dashboard = orchestrator.dashboard
        self.health = orchestrator.health

    async def monitor_until_complete(self) -> None:
        """
        Monitor tournament execution until completion or shutdown.

        Continuously polls tournament status and broadcasts updates
        to the dashboard every 5 seconds.
        """
        logger.info("Monitoring tournament execution")

        while True:
            await asyncio.sleep(5)

            # Check for shutdown signal
            if self.orchestrator.shutdown_requested:
                logger.warning("Shutdown requested - stopping tournament monitoring")
                break

            # Update status
            if not await self._update_tournament_status():
                continue

            # Check if complete
            if await self._check_tournament_complete():
                break

    async def _update_tournament_status(self) -> bool:
        """
        Fetch and broadcast tournament status.

        Returns:
            True if status fetched successfully, False otherwise
        """
        # Get tournament status
        status = await self.tournament.monitor_tournament()

        if not status:
            logger.warning("Failed to get tournament status")
            return False

        # Update health status
        health_status = {
            agent_id: status_val.value
            for agent_id, status_val in self.health.health_status.items()
        }
        await self.dashboard.broadcast_update("health", health_status)

        # Broadcast tournament status
        await self.dashboard.broadcast_update("tournament", status)

        # Broadcast standings
        state = self.tournament.get_current_state()
        if state.standings:
            await self.dashboard.broadcast_update("standings", state.standings)

        # Log current status
        logger.info(
            "Tournament status",
            stage=status.get("stage"),
            round=status.get("current_round"),
            total_rounds=status.get("total_rounds")
        )

        return True

    async def _check_tournament_complete(self) -> bool:
        """
        Check if tournament is complete.

        Returns:
            True if tournament is complete, False otherwise
        """
        state = self.tournament.get_current_state()

        if state.is_tournament_complete():
            logger.info("Tournament completed - all matches finished!")

            # Log winner
            winner = state.standings[0]["player_id"] if state.standings else "N/A"
            logger.info("Final standings", winner=winner)

            # Broadcast completion
            await self.dashboard.broadcast_update("tournament", {
                "status": "COMPLETED",
                "final_standings": state.standings
            })

            logger.info("Initiating graceful shutdown of all agents...")
            return True

        return False
