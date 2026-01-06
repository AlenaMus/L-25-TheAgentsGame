"""
Unit tests for HealthMonitor.

Tests health checking and recovery callbacks.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from orchestrator.monitoring.health_monitor import (
    HealthMonitor,
    HealthStatus
)
from orchestrator.config import AgentConfig


@pytest.fixture
def agent_configs():
    """Create test agent configurations."""
    return {
        "test_agent": AgentConfig(
            agent_id="test_agent",
            agent_type="PLAYER",
            port=8101,
            working_dir="/test",
            startup_command=["python", "main.py"],
            health_endpoint="http://localhost:8101/health",
            dependencies=[]
        )
    }


@pytest.fixture
def health_monitor(agent_configs):
    """Create health monitor instance."""
    return HealthMonitor(
        agent_configs,
        check_interval=1,
        failure_threshold=3
    )


@pytest.mark.asyncio
async def test_check_agent_healthy(health_monitor):
    """Test health check for healthy agent."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        status = await health_monitor.check_agent(
            "test_agent", "http://localhost:8101/health"
        )

        assert status == HealthStatus.HEALTHY
        assert health_monitor.failure_counts.get("test_agent", 0) == 0


@pytest.mark.asyncio
async def test_check_agent_single_failure(health_monitor):
    """Test single health check failure."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        status = await health_monitor.check_agent(
            "test_agent", "http://localhost:8101/health"
        )

        # Still healthy after 1 failure (threshold is 3)
        assert status == HealthStatus.HEALTHY
        assert health_monitor.failure_counts["test_agent"] == 1


@pytest.mark.asyncio
async def test_check_agent_unhealthy_after_threshold(health_monitor):
    """Test agent becomes unhealthy after threshold failures."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        # Fail 3 times
        for _ in range(3):
            status = await health_monitor.check_agent(
                "test_agent", "http://localhost:8101/health"
            )

        assert status == HealthStatus.UNHEALTHY
        assert health_monitor.failure_counts["test_agent"] == 3


@pytest.mark.asyncio
async def test_recovery_callback_triggered(health_monitor):
    """Test recovery callback is triggered when agent becomes unhealthy."""
    callback_called = False

    async def recovery_callback(agent_id):
        nonlocal callback_called
        callback_called = True
        assert agent_id == "test_agent"

    health_monitor.register_recovery_callback("test_agent", recovery_callback)

    with patch("httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            side_effect=Exception("Connection refused")
        )

        # Trigger recovery by marking unhealthy
        await health_monitor._trigger_recovery("test_agent")

        assert callback_called is True


@pytest.mark.asyncio
async def test_recovery_on_status_change(health_monitor):
    """Test recovery is triggered when status changes to unhealthy."""
    recovery_called = False

    async def recovery_callback(agent_id):
        nonlocal recovery_called
        recovery_called = True

    health_monitor.register_recovery_callback("test_agent", recovery_callback)

    # Simulate health status change
    health_monitor.health_status["test_agent"] = HealthStatus.HEALTHY
    await health_monitor._trigger_recovery("test_agent")

    assert recovery_called is True


@pytest.mark.asyncio
async def test_start_stop_monitoring(health_monitor):
    """Test starting and stopping health monitor."""
    await health_monitor.start()
    assert health_monitor._running is True
    assert health_monitor._task is not None

    await health_monitor.stop()
    assert health_monitor._running is False


@pytest.mark.asyncio
async def test_failure_count_reset_on_success(health_monitor):
    """Test failure count resets when agent becomes healthy again."""
    # Set initial failure count
    health_monitor.failure_counts["test_agent"] = 2

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(
            return_value=mock_response
        )

        status = await health_monitor.check_agent(
            "test_agent", "http://localhost:8101/health"
        )

        assert status == HealthStatus.HEALTHY
        assert health_monitor.failure_counts["test_agent"] == 0
