"""
Agent Manager - Manages agent lifecycle for integration tests.

Starts/stops agents in separate processes with proper cleanup.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Dict, Optional, List
import time

from .mcp_client import MCPClient


class AgentProcess:
    """Represents a running agent process."""

    def __init__(
        self,
        agent_type: str,
        agent_id: str,
        port: int,
        process: subprocess.Popen,
        endpoint: str
    ):
        """
        Initialize agent process.

        Args:
            agent_type: Type of agent (player, referee, league_manager)
            agent_id: Unique agent identifier
            port: Port the agent is listening on
            process: Subprocess running the agent
            endpoint: Full HTTP endpoint URL
        """
        self.agent_type = agent_type
        self.agent_id = agent_id
        self.port = port
        self.process = process
        self.endpoint = endpoint

    def terminate(self) -> None:
        """Terminate the agent process."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class AgentManager:
    """
    Manages multiple agent processes for integration testing.

    Handles starting agents, health checks, and cleanup.
    """

    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize agent manager.

        Args:
            project_root: Project root directory path
        """
        if project_root is None:
            # Assume tests are in <project_root>/tests/integration
            project_root = Path(__file__).parent.parent.parent.parent

        self.project_root = Path(project_root)
        self.agents: Dict[str, AgentProcess] = {}
        self.mcp_client = MCPClient(timeout=10)

    async def start_player(
        self,
        agent_id: str,
        port: int,
        wait_for_ready: bool = True
    ) -> AgentProcess:
        """
        Start a player agent.

        Args:
            agent_id: Player ID (e.g., "P01")
            port: Port to listen on
            wait_for_ready: Wait for agent to be ready

        Returns:
            AgentProcess: Running agent process
        """
        return await self._start_agent(
            agent_type="player",
            agent_id=agent_id,
            port=port,
            module_path="player_agent.main",
            wait_for_ready=wait_for_ready
        )

    async def start_referee(
        self,
        agent_id: str,
        port: int,
        wait_for_ready: bool = True
    ) -> AgentProcess:
        """
        Start a referee agent.

        Args:
            agent_id: Referee ID (e.g., "REF01")
            port: Port to listen on
            wait_for_ready: Wait for agent to be ready

        Returns:
            AgentProcess: Running agent process
        """
        return await self._start_agent(
            agent_type="referee",
            agent_id=agent_id,
            port=port,
            module_path="referee.main",
            wait_for_ready=wait_for_ready
        )

    async def start_league_manager(
        self,
        port: int,
        wait_for_ready: bool = True
    ) -> AgentProcess:
        """
        Start league manager agent.

        Args:
            port: Port to listen on
            wait_for_ready: Wait for agent to be ready

        Returns:
            AgentProcess: Running agent process
        """
        return await self._start_agent(
            agent_type="league_manager",
            agent_id="LM01",
            port=port,
            module_path="league_manager.main",
            wait_for_ready=wait_for_ready
        )

    async def _start_agent(
        self,
        agent_type: str,
        agent_id: str,
        port: int,
        module_path: str,
        wait_for_ready: bool
    ) -> AgentProcess:
        """
        Internal method to start an agent.

        Args:
            agent_type: Type of agent
            agent_id: Agent identifier
            port: Port number
            module_path: Python module path
            wait_for_ready: Wait for ready state

        Returns:
            AgentProcess: Running agent

        Raises:
            RuntimeError: If agent fails to start
        """
        agent_dir = self.project_root / "agents" / f"{agent_type}_agent"
        if not agent_dir.exists():
            # Try alternative naming
            agent_dir = self.project_root / "agents" / agent_type

        if not agent_dir.exists():
            raise RuntimeError(f"Agent directory not found: {agent_dir}")

        # Build command to run uvicorn with the agent's app
        env = {
            "PYTHONPATH": str(agent_dir / "src"),
            "AGENT_ID": agent_id,
            "PORT": str(port),
        }

        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            f"{module_path}:app",
            "--host",
            "0.0.0.0",
            "--port",
            str(port),
        ]

        # Start process
        process = subprocess.Popen(
            cmd,
            cwd=str(agent_dir),
            env={**subprocess.os.environ, **env},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        endpoint = f"http://localhost:{port}/mcp"
        agent_process = AgentProcess(
            agent_type=agent_type,
            agent_id=agent_id,
            port=port,
            process=process,
            endpoint=endpoint
        )

        self.agents[agent_id] = agent_process

        # Wait for agent to be ready
        if wait_for_ready:
            await self._wait_for_ready(agent_process)

        return agent_process

    async def _wait_for_ready(
        self,
        agent: AgentProcess,
        timeout: float = 30.0,
        poll_interval: float = 0.5
    ) -> None:
        """
        Wait for agent to be ready.

        Args:
            agent: Agent process to check
            timeout: Maximum wait time in seconds
            poll_interval: Time between health checks

        Raises:
            RuntimeError: If agent doesn't become ready
        """
        start_time = time.time()

        while time.time() - start_time < timeout:
            # Check if process crashed
            if agent.process.poll() is not None:
                raise RuntimeError(
                    f"Agent {agent.agent_id} crashed during startup"
                )

            # Check if agent responds to health check
            if await self.mcp_client.health_check(agent.endpoint):
                return

            await asyncio.sleep(poll_interval)

        raise RuntimeError(
            f"Agent {agent.agent_id} failed to become ready "
            f"within {timeout}s"
        )

    async def stop_agent(self, agent_id: str) -> None:
        """
        Stop a specific agent.

        Args:
            agent_id: Agent identifier to stop
        """
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.terminate()
            del self.agents[agent_id]

    async def stop_all(self) -> None:
        """Stop all running agents."""
        for agent_id in list(self.agents.keys()):
            await self.stop_agent(agent_id)

    async def cleanup(self) -> None:
        """Cleanup all resources."""
        await self.stop_all()
        await self.mcp_client.close()
