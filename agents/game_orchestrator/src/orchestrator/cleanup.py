"""
Cleanup coordination for Game Orchestrator.

Handles graceful shutdown of all orchestrator components.
"""

import asyncio
from loguru import logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .main import GameOrchestrator


class CleanupCoordinator:
    """Coordinates graceful shutdown of all components."""

    def __init__(self, orchestrator: 'GameOrchestrator'):
        """
        Initialize cleanup coordinator.

        Args:
            orchestrator: Parent GameOrchestrator instance
        """
        self.orchestrator = orchestrator

    async def execute_shutdown(self) -> None:
        """Execute complete shutdown sequence."""
        logger.info("=== Initiating Orchestrator Cleanup ===")

        await self._stop_dashboard()
        await self._stop_health_monitoring()
        await self._stop_all_agents()

        logger.info("=== Orchestrator Shutdown Complete ===")

    async def _stop_dashboard(self) -> None:
        """Stop dashboard server."""
        if self.orchestrator.dashboard_task and not self.orchestrator.dashboard_task.done():
            self.orchestrator.dashboard_task.cancel()
            try:
                await self.orchestrator.dashboard_task
            except asyncio.CancelledError:
                logger.info("Dashboard stopped")

    async def _stop_health_monitoring(self) -> None:
        """Stop health monitoring service."""
        await self.orchestrator.health.stop()

    async def _stop_all_agents(self) -> None:
        """Stop all started agents."""
        agents_to_stop = list(self.orchestrator.lifecycle.started_agents)
        logger.info(f"Stopping {len(agents_to_stop)} agents")

        for agent_id in agents_to_stop:
            await self.orchestrator.lifecycle.stop_agent(agent_id)
