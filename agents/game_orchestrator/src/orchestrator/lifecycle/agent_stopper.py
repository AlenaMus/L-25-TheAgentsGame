"""
Agent shutdown logic.

Handles graceful termination and forced killing of agent processes.
"""

import subprocess
from typing import Dict
from loguru import logger


class AgentStopper:
    """Handles agent stop and restart operations."""

    def __init__(
        self,
        processes: Dict[str, subprocess.Popen],
        started_agents: set
    ):
        """
        Initialize agent stopper.

        Args:
            processes: Dictionary of running processes
            started_agents: Set of successfully started agent IDs
        """
        self.processes = processes
        self.started_agents = started_agents

    async def stop_agent(self, agent_id: str) -> bool:
        """
        Stop a running agent.

        Args:
            agent_id: Agent identifier

        Returns:
            True if agent stopped successfully
        """
        if agent_id not in self.processes:
            logger.warning(f"Agent {agent_id} not running")
            return True

        try:
            process = self.processes[agent_id]
            process.terminate()

            # Wait for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {agent_id}")
                process.kill()
                process.wait()

            del self.processes[agent_id]
            self.started_agents.discard(agent_id)
            logger.info(f"Agent {agent_id} stopped")
            return True

        except Exception as e:
            logger.error(f"Error stopping {agent_id}", error=str(e))
            return False
