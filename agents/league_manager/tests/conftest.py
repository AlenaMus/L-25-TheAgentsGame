"""
Pytest configuration and fixtures for League Manager tests.
"""

import pytest
from league_manager.storage.agent_registry import AgentRegistry
from league_manager.storage.league_store import LeagueStore
from league_manager.standings.calculator import StandingsCalculator


@pytest.fixture
def agent_registry(tmp_path):
    """Provide agent registry with temporary storage."""
    return AgentRegistry(str(tmp_path), "test_league")


@pytest.fixture
def league_store(tmp_path):
    """Provide league store with temporary storage."""
    return LeagueStore(str(tmp_path), "test_league")


@pytest.fixture
def standings_calc():
    """Provide standings calculator."""
    return StandingsCalculator()
