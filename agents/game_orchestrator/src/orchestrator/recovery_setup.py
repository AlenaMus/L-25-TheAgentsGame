"""
Error recovery setup for Game Orchestrator.

Configures error handlers and recovery callbacks for agent failures.
"""

from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import GameOrchestrator


class RecoverySetup:
    """Configures error recovery for orchestrator."""

    def __init__(self, orchestrator: 'GameOrchestrator'):
        """
        Initialize recovery setup.

        Args:
            orchestrator: Parent GameOrchestrator instance
        """
        self.orchestrator = orchestrator
        self.config = orchestrator.config
        self.recovery = orchestrator.recovery
        self.tournament = orchestrator.tournament
        self.lifecycle = orchestrator.lifecycle
        self.health = orchestrator.health
        self.dashboard = orchestrator.dashboard

    def setup_handlers(self) -> None:
        """Configure all error recovery handlers."""
        self._setup_crash_handler()
        self._setup_health_callbacks()

    def _setup_crash_handler(self) -> None:
        """Setup handler for agent crash recovery."""

        async def handle_agent_crash(context: dict):
            """Handle agent crash recovery with exponential backoff."""
            agent_id = context.get("agent_id")
            logger.error(f"Agent {agent_id} crashed", context=context)

            # Pause tournament if critical agent
            if agent_id == "league_manager":
                await self.tournament.pause_tournament()

            # Attempt restart with exponential backoff
            success = await self.recovery.restart_agent(
                agent_id,
                self.lifecycle.restart_agent,
                max_retries=3
            )

            if success:
                logger.info(f"Agent {agent_id} recovered")
                if agent_id == "league_manager":
                    await self.tournament.resume_tournament()
            else:
                logger.critical(f"Failed to recover {agent_id}")
                await self.dashboard.broadcast_update("error", {
                    "type": "AGENT_CRASH_UNRECOVERABLE",
                    "agent_id": agent_id
                })

        self.recovery.register_handler("AGENT_CRASH", handle_agent_crash)

    def _setup_health_callbacks(self) -> None:
        """Register health monitoring recovery callbacks for all agents."""
        for agent_id in self.config.agents.keys():
            self.health.register_recovery_callback(
                agent_id,
                lambda aid=agent_id: self.recovery.handle_error(
                    "AGENT_CRASH", {"agent_id": aid}
                )
            )
