"""
Pytest configuration for system-level integration tests.

Provides fixtures for managing agents during tests.
"""

import pytest
import asyncio
from pathlib import Path

from tests.integration.utils import AgentManager, PortManager


@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.

    Scope: session - shared across all tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def project_root():
    """
    Get project root directory.

    Returns:
        Path: Project root path
    """
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def port_manager():
    """
    Port manager for allocating unique ports.

    Scope: session - shared across all tests.
    """
    manager = PortManager(start_port=9000)
    yield manager
    manager.reset()


@pytest.fixture
async def agent_manager(project_root):
    """
    Agent manager for starting/stopping agents.

    Scope: function - new instance per test.
    Automatically cleans up agents after test.
    """
    manager = AgentManager(project_root)
    yield manager
    await manager.cleanup()


@pytest.fixture
async def league_manager(agent_manager, port_manager):
    """
    Start a league manager agent.

    Returns:
        AgentProcess: Running league manager
    """
    port = port_manager.allocate()
    agent = await agent_manager.start_league_manager(port)
    yield agent
    port_manager.release(port)


@pytest.fixture
async def referee(agent_manager, port_manager):
    """
    Start a referee agent.

    Returns:
        AgentProcess: Running referee
    """
    port = port_manager.allocate()
    agent = await agent_manager.start_referee("REF01", port)
    yield agent
    port_manager.release(port)


@pytest.fixture
async def player(agent_manager, port_manager):
    """
    Start a single player agent.

    Returns:
        AgentProcess: Running player
    """
    port = port_manager.allocate()
    agent = await agent_manager.start_player("P01", port)
    yield agent
    port_manager.release(port)


@pytest.fixture
async def two_players(agent_manager, port_manager):
    """
    Start two player agents.

    Returns:
        tuple: (player1, player2) AgentProcess instances
    """
    port1 = port_manager.allocate()
    port2 = port_manager.allocate()

    player1 = await agent_manager.start_player("P01", port1)
    player2 = await agent_manager.start_player("P02", port2)

    yield (player1, player2)

    port_manager.release(port1)
    port_manager.release(port2)


@pytest.fixture
async def three_players(agent_manager, port_manager):
    """
    Start three player agents.

    Returns:
        tuple: (player1, player2, player3) AgentProcess instances
    """
    port1 = port_manager.allocate()
    port2 = port_manager.allocate()
    port3 = port_manager.allocate()

    player1 = await agent_manager.start_player("P01", port1)
    player2 = await agent_manager.start_player("P02", port2)
    player3 = await agent_manager.start_player("P03", port3)

    yield (player1, player2, player3)

    port_manager.release(port1)
    port_manager.release(port2)
    port_manager.release(port3)
