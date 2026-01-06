"""
Agent startup logic with dependency checking.

Handles subprocess spawning and startup verification.
"""

import asyncio
import subprocess
from pathlib import Path
from typing import Dict
from loguru import logger

from ..config import AgentConfig


class AgentStartupError(Exception):
    """Raised when agent fails to start."""
    pass


class AgentStarter:
    """Handles agent startup operations."""

    def __init__(
        self,
        agents: Dict[str, AgentConfig],
        processes: Dict[str, subprocess.Popen],
        started_agents: set
    ):
        """
        Initialize agent starter.

        Args:
            agents: Dictionary of agent configurations
            processes: Dictionary of running processes
            started_agents: Set of successfully started agent IDs
        """
        self.agents = agents
        self.processes = processes
        self.started_agents = started_agents

    async def start_agent(
        self, agent_id: str, timeout: int = 30
    ) -> bool:
        """Start a single agent with dependency checking."""
        if agent_id in self.started_agents:
            logger.warning(f"Agent {agent_id} already started")
            return True

        agent = self.agents[agent_id]

        # Check dependencies
        for dep in agent.dependencies:
            if dep not in self.started_agents:
                raise AgentStartupError(
                    f"Dependency {dep} not started for {agent_id}"
                )

        logger.info(f"Starting agent {agent_id}", agent_type=agent.agent_type)

        try:
            process = self._spawn_process(agent_id, agent)
            self.processes[agent_id] = process
            logger.info(f"Process spawned for {agent_id}", pid=process.pid)

            # Wait for startup
            grace_period = max(5, timeout / 5)
            logger.debug(f"Waiting {grace_period}s for {agent_id} to start")
            await asyncio.sleep(grace_period)

            # Check process didn't immediately crash
            poll_result = process.poll()
            if poll_result is not None:
                logger.error(
                    f"Agent {agent_id} process exited during startup",
                    exit_code=poll_result,
                    pid=process.pid
                )
                raise AgentStartupError(
                    f"{agent_id} process exited with code {poll_result}"
                )

            self.started_agents.add(agent_id)
            logger.info(f"Agent {agent_id} started successfully", pid=process.pid)
            return True

        except Exception as e:
            logger.error(f"Failed to start {agent_id}", error=str(e))
            raise AgentStartupError(f"Failed to start {agent_id}: {e}")

    def _spawn_process(
        self, agent_id: str, agent: AgentConfig
    ) -> subprocess.Popen:
        """Spawn agent subprocess."""
        # Convert working dir to absolute path
        working_dir = Path(agent.working_dir).resolve()

        # Convert command to use absolute paths if first arg is relative
        startup_cmd = agent.startup_command.copy()
        first_arg = Path(startup_cmd[0])
        if not first_arg.is_absolute():
            first_arg = (working_dir / first_arg).resolve()
            startup_cmd[0] = str(first_arg)

        # Prepare environment variables
        env = dict(subprocess.os.environ)  # Copy parent environment
        env["AGENT_ID"] = agent_id
        env["PORT"] = str(agent.port)

        # Log startup details
        logger.info(
            f"Starting {agent_id}",
            command=" ".join(startup_cmd),
            working_dir=str(working_dir),
            env_vars=f"AGENT_ID={agent_id}, PORT={agent.port}"
        )

        try:
            return subprocess.Popen(
                startup_cmd,
                cwd=str(working_dir),
                env=env,
                stdout=None,
                stderr=None,
            )
        except FileNotFoundError as e:
            logger.error(
                f"Failed to start {agent_id}: executable not found",
                command=agent.startup_command[0],
                working_dir=agent.working_dir,
                error=str(e)
            )
            raise AgentStartupError(
                f"Executable not found: {agent.startup_command[0]}"
            )
