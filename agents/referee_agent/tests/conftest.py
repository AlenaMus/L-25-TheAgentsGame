"""
Pytest configuration and fixtures for referee tests.

Provides shared fixtures for testing.
"""

import pytest
from unittest.mock import AsyncMock


@pytest.fixture
def mock_mcp_client():
    """Create mock MCP client for testing."""
    client = AsyncMock()
    client.call_tool = AsyncMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
def sample_match_params():
    """Sample match parameters for testing."""
    return {
        "match_id": "R1M1",
        "round_id": "1",
        "player_A_id": "P01",
        "player_B_id": "P02",
        "player_A_endpoint": "http://localhost:8101/mcp",
        "player_B_endpoint": "http://localhost:8102/mcp"
    }
