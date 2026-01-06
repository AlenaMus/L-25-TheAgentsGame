"""
Agent startup coordination for Game Orchestrator.

Handles the sequential startup of agents in correct dependency order.
"""

import asyncio
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import GameOrchestrator


class StartupCoordinator:
    """Coordinates agent startup in correct dependency order."""

    def __init__(self, orchestrator: 'GameOrchestrator'):
        """
        Initialize startup coordinator.

        Args:
            orchestrator: Parent GameOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.config = orchestrator.config
        self.lifecycle = orchestrator.lifecycle

    async def execute_startup_sequence(self) -> bool:
        """
        Execute complete agent startup sequence.

        Returns:
            True if all agents started successfully
        """
        try:
            # Stage 1: Start League Manager
            if not await self._start_league_manager():
                return False

            await asyncio.sleep(self.config.orchestrator.startup_grace_period)

            # Stage 2: Start Referees
            if not await self._start_referees():
                return False

            await asyncio.sleep(self.config.orchestrator.startup_grace_period)

            # Stage 3: Start Players
            if not await self._start_players():
                return False

            await asyncio.sleep(self.config.orchestrator.startup_grace_period)

            # Stage 4: Verify Communication (currently skipped)
            self._log_verification_skip()

            return True

        except Exception as e:
            logger.critical("Startup sequence failed", error=str(e))
            return False

    async def _start_league_manager(self) -> bool:
        """Start League Manager agent."""
        logger.info("=== Stage 1: Starting League Manager ===")

        league_mgr_id = self.config.get_agents_by_type("LEAGUE_MANAGER")[0].agent_id

        try:
            success = await self.lifecycle.start_agent(
                league_mgr_id,
                timeout=self.config.orchestrator.agent_startup_timeout
            )

            if not success:
                logger.error("Failed to start League Manager")
                return False

            return True

        except Exception as e:
            logger.error(
                "Failed to start League Manager",
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            return False

    async def _start_referees(self) -> bool:
        """Start all referee agents."""
        logger.info("=== Stage 2: Starting Referees ===")

        referees = [
            a.agent_id for a in self.config.get_agents_by_type("REFEREE")
        ]

        for ref_id in referees:
            await self.lifecycle.start_agent(
                ref_id,
                timeout=self.config.orchestrator.agent_startup_timeout
            )

        return True

    async def _start_players(self) -> bool:
        """Start all player agents."""
        logger.info("=== Stage 3: Starting Players ===")

        players = [
            a.agent_id for a in self.config.get_agents_by_type("PLAYER")
        ]

        for player_id in players:
            await self.lifecycle.start_agent(
                player_id,
                timeout=self.config.orchestrator.agent_startup_timeout
            )

        return True

    def _log_verification_skip(self) -> None:
        """Log that communication verification is skipped."""
        logger.info("=== Stage 4: Skipping Communication Verification ===")
        logger.warning(
            "Communication verification disabled - proceeding to tournament"
        )
        logger.info("Proceeding without verification")
