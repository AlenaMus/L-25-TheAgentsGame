"""
Health Monitor - Continuous health monitoring with automatic recovery.

Performs periodic health checks on all agents and triggers recovery callbacks.
"""

import asyncio
from enum import Enum
from typing import Dict, Callable, Optional
import httpx
from loguru import logger

from ..config import AgentConfig


class HealthStatus(Enum):
    """Agent health status."""
    HEALTHY = "HEALTHY"
    UNHEALTHY = "UNHEALTHY"
    UNKNOWN = "UNKNOWN"


class HealthMonitor:
    """Monitors agent health with automatic recovery."""

    def __init__(
        self,
        agents: Dict[str, AgentConfig],
        check_interval: int = 5,
        failure_threshold: int = 3
    ):
        """
        Initialize health monitor.

        Args:
            agents: Dictionary mapping agent_id to AgentConfig
            check_interval: Seconds between health checks
            failure_threshold: Failures before marking UNHEALTHY
        """
        self.agents = agents
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold

        self.health_status: Dict[str, HealthStatus] = {}
        self.failure_counts: Dict[str, int] = {}
        self.recovery_callbacks: Dict[str, Callable] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start health monitoring loop."""
        if self._running:
            logger.warning("Health monitor already running")
            return

        self._running = True
        logger.info("Starting health monitor", interval=self.check_interval)
        self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self) -> None:
        """Stop health monitoring loop."""
        if not self._running:
            return

        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Health monitor stopped")

    async def check_agent(self, agent_id: str, endpoint: str) -> HealthStatus:
        """
        Check health of a single agent.

        Args:
            agent_id: Agent identifier
            endpoint: Health endpoint URL

        Returns:
            HealthStatus of the agent
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(endpoint)

                if response.status_code == 200:
                    self.failure_counts[agent_id] = 0
                    return HealthStatus.HEALTHY
                else:
                    logger.warning(
                        f"Agent {agent_id} returned {response.status_code}"
                    )
                    return self._handle_failure(agent_id)

        except Exception as e:
            logger.debug(
                f"Health check failed for {agent_id}", error=str(e)
            )
            return self._handle_failure(agent_id)

    def register_recovery_callback(
        self, agent_id: str, callback: Callable
    ) -> None:
        """
        Register callback for agent recovery.

        Args:
            agent_id: Agent identifier
            callback: Async function to call when agent becomes UNHEALTHY
        """
        self.recovery_callbacks[agent_id] = callback
        logger.debug(f"Registered recovery callback for {agent_id}")

    def _handle_failure(self, agent_id: str) -> HealthStatus:
        """Handle health check failure and track count."""
        count = self.failure_counts.get(agent_id, 0) + 1
        self.failure_counts[agent_id] = count

        if count >= self.failure_threshold:
            logger.error(
                f"Agent {agent_id} UNHEALTHY",
                failures=count
            )
            return HealthStatus.UNHEALTHY
        else:
            logger.debug(
                f"Agent {agent_id} failure {count}/{self.failure_threshold}"
            )
            return HealthStatus.HEALTHY

    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)

                # Check all agents
                for agent_id, config in self.agents.items():
                    status = await self.check_agent(
                        agent_id, config.health_endpoint
                    )
                    old_status = self.health_status.get(agent_id)
                    self.health_status[agent_id] = status

                    # Trigger recovery if became unhealthy
                    if (status == HealthStatus.UNHEALTHY and
                        old_status != HealthStatus.UNHEALTHY):
                        await self._trigger_recovery(agent_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Monitor loop error", error=str(e))

    async def _trigger_recovery(self, agent_id: str) -> None:
        """Trigger recovery callback for unhealthy agent."""
        callback = self.recovery_callbacks.get(agent_id)
        if callback:
            logger.info(f"Triggering recovery for {agent_id}")
            try:
                await callback(agent_id)
            except Exception as e:
                logger.error(
                    f"Recovery callback failed for {agent_id}",
                    error=str(e)
                )
