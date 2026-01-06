"""
Pytest configuration and fixtures for Player Agent P01.
"""

import pytest
import pytest_asyncio
from pathlib import Path


@pytest.fixture
def agent_config():
    """
    Provide test configuration.

    Returns:
        Config: Test configuration instance
    """
    from player_agent.config import Config
    return Config(
        agent_id="P01",
        port=8101,
        league_manager_url="http://localhost:8000/mcp"
    )


@pytest.fixture
def logger():
    """
    Provide test logger.

    Returns:
        Logger: Configured logger instance
    """
    from player_agent.utils.logger import logger, setup_logger
    setup_logger("P01")
    return logger


@pytest.fixture(scope="session")
def event_loop_policy():
    """
    Set event loop policy for async tests.

    Required for pytest-asyncio compatibility.
    """
    import asyncio
    return asyncio.get_event_loop_policy()
