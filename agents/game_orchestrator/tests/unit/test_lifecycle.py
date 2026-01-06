"""
Unit tests for AgentLifecycleManager.

Tests agent startup, shutdown, and dependency management.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from orchestrator.lifecycle.agent_manager import (
    AgentLifecycleManager,
    AgentStartupError
)
from orchestrator.config import AgentConfig


@pytest.fixture
def agent_configs():
    """Create test agent configurations."""
    return {
        "league_manager": AgentConfig(
            agent_id="league_manager",
            agent_type="LEAGUE_MANAGER",
            port=8000,
            working_dir="/test/league",
            startup_command=["python", "main.py"],
            health_endpoint="http://localhost:8000/health",
            dependencies=[]
        ),
        "REF01": AgentConfig(
            agent_id="REF01",
            agent_type="REFEREE",
            port=8001,
            working_dir="/test/referee",
            startup_command=["python", "main.py"],
            health_endpoint="http://localhost:8001/health",
            dependencies=["league_manager"]
        ),
        "P01": AgentConfig(
            agent_id="P01",
            agent_type="PLAYER",
            port=8101,
            working_dir="/test/player",
            startup_command=["python", "main.py"],
            health_endpoint="http://localhost:8101/health",
            dependencies=["league_manager"]
        )
    }


@pytest.fixture
def lifecycle_manager(agent_configs):
    """Create lifecycle manager instance."""
    return AgentLifecycleManager(agent_configs)


@pytest.mark.asyncio
async def test_start_agent_success(lifecycle_manager):
    """Test successful agent startup."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None  # Process running
        mock_popen.return_value = mock_process

        success = await lifecycle_manager.start_agent(
            "league_manager", timeout=1
        )

        assert success is True
        assert "league_manager" in lifecycle_manager.started_agents
        assert lifecycle_manager.processes["league_manager"] == mock_process


@pytest.mark.asyncio
async def test_start_agent_missing_dependency(lifecycle_manager):
    """Test starting agent without required dependency."""
    with pytest.raises(AgentStartupError) as exc:
        await lifecycle_manager.start_agent("REF01")

    assert "Dependency" in str(exc.value)
    assert "league_manager" in str(exc.value)


@pytest.mark.asyncio
async def test_start_agent_already_started(lifecycle_manager):
    """Test starting already running agent."""
    lifecycle_manager.started_agents.add("league_manager")

    with patch("subprocess.Popen"):
        success = await lifecycle_manager.start_agent(
            "league_manager", timeout=1
        )

    assert success is True


@pytest.mark.asyncio
async def test_start_all_agents(lifecycle_manager):
    """Test starting all agents in correct order."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        results = await lifecycle_manager.start_all_agents()

        # All agents should start successfully
        assert results["league_manager"] is True
        assert results["REF01"] is True
        assert results["P01"] is True

        # League Manager should start first
        assert "league_manager" in lifecycle_manager.started_agents


@pytest.mark.asyncio
async def test_stop_agent(lifecycle_manager):
    """Test stopping a running agent."""
    mock_process = MagicMock()
    lifecycle_manager.processes["league_manager"] = mock_process
    lifecycle_manager.started_agents.add("league_manager")

    success = await lifecycle_manager.stop_agent("league_manager")

    assert success is True
    mock_process.terminate.assert_called_once()
    assert "league_manager" not in lifecycle_manager.processes
    assert "league_manager" not in lifecycle_manager.started_agents


@pytest.mark.asyncio
async def test_restart_agent(lifecycle_manager):
    """Test restarting an agent."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_popen.return_value = mock_process

        # Start agent first
        lifecycle_manager.processes["league_manager"] = mock_process
        lifecycle_manager.started_agents.add("league_manager")

        # Restart
        success = await lifecycle_manager.restart_agent("league_manager")

        assert success is True
        assert "league_manager" in lifecycle_manager.started_agents


@pytest.mark.asyncio
async def test_agent_crash_on_startup(lifecycle_manager):
    """Test handling agent that crashes immediately."""
    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = 1  # Process exited
        mock_process.communicate.return_value = ("", "Error")
        mock_popen.return_value = mock_process

        with pytest.raises(AgentStartupError) as exc:
            await lifecycle_manager.start_agent(
                "league_manager", timeout=1
            )

        assert "crashed" in str(exc.value).lower()
