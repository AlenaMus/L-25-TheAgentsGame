"""
Agent Lifecycle Manager - Start/stop/restart agents with dependency management.

Handles subprocess management and dependency-aware startup sequencing.
"""

import asyncio
import subprocess
from typing import Dict
from loguru import logger

from ..config import AgentConfig
from .agent_starter import AgentStarter, AgentStartupError
from .agent_stopper import AgentStopper


class AgentLifecycleManager:
    """Manages agent lifecycle with dependency handling."""

    def __init__(self, agents: Dict[str, AgentConfig]):
        """
        Initialize lifecycle manager.

        Args:
            agents: Dictionary mapping agent_id to AgentConfig
        """
        self.agents = agents
        self.processes: Dict[str, subprocess.Popen] = {}
        self.started_agents: set = set()

        # Initialize helper components
        self.starter = AgentStarter(
            self.agents,
            self.processes,
            self.started_agents
        )
        self.stopper = AgentStopper(
            self.processes,
            self.started_agents
        )

    async def start_agent(
        self, agent_id: str, timeout: int = 30
    ) -> bool:
        """
        Start a single agent with dependency checking.

        Args:
            agent_id: Agent identifier
            timeout: Startup timeout in seconds

        Returns:
            True if agent started successfully

        Raises:
            AgentStartupError: If dependencies not met or startup fails
        """
        return await self.starter.start_agent(agent_id, timeout)

    async def start_all_agents(self) -> Dict[str, bool]:
        """
        Start all agents in correct dependency order.

        Returns:
            Dictionary mapping agent_id to success status
        """
        results = {}

        # Start by tier: League Manager → Referees → Players
        tiers = [
            self._get_agents_by_type("LEAGUE_MANAGER"),
            self._get_agents_by_type("REFEREE"),
            self._get_agents_by_type("PLAYER"),
        ]

        for tier in tiers:
            # Start all agents in tier simultaneously
            tasks = [self.start_agent(agent_id) for agent_id in tier]
            tier_results = await asyncio.gather(
                *tasks, return_exceptions=True
            )

            for agent_id, result in zip(tier, tier_results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Failed to start {agent_id}", error=str(result)
                    )
                    results[agent_id] = False
                else:
                    results[agent_id] = result

        return results

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a running agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent stopped successfully
        """
        return await self.stopper.stop_agent(agent_id)

    async def restart_agent(self, agent_id: str) -> bool:
        """
        Restart an agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if restart successful
        """
        logger.info(f"Restarting agent {agent_id}")
        await self.stop_agent(agent_id)
        return await self.start_agent(agent_id)

    def _get_agents_by_type(self, agent_type: str) -> list:
        """Get list of agent IDs of given type."""
        return [
            agent_id for agent_id, config in self.agents.items()
            if config.agent_type == agent_type
        ]


__all__ = ["AgentLifecycleManager", "AgentStartupError"]
