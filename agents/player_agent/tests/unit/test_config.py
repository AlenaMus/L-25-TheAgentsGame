"""
Unit tests for Configuration.

Tests configuration loading and management including:
- Default values
- Environment variable loading
- Credential storage
- Configuration validation
"""

import pytest
from unittest.mock import patch
import os

from player_agent.config import Config


def test_config_default_values():
    """
    Test that config has correct default values.

    Arrange: Create Config instance
    Act: Check default values
    Assert: All defaults are correct
    """
    config = Config()

    assert config.agent_id == "P01"
    assert config.temp_name == "player_p01"
    assert config.display_name == "Agent P01"
    assert config.port == 8101
    assert config.league_manager_url == "http://localhost:8000/mcp"
    assert config.auth_token is None
    assert config.league_id is None


def test_config_custom_agent_id():
    """
    Test creating config with custom agent_id.

    Arrange: Pass custom agent_id
    Act: Create Config
    Assert: agent_id is set correctly
    """
    config = Config(agent_id="P99")

    assert config.agent_id == "P99"


def test_config_custom_port():
    """
    Test creating config with custom port.

    Arrange: Pass custom port
    Act: Create Config
    Assert: port is set correctly
    """
    config = Config(port=9000)

    assert config.port == 9000


def test_config_custom_league_manager_url():
    """
    Test creating config with custom league manager URL.

    Arrange: Pass custom URL
    Act: Create Config
    Assert: URL is set correctly
    """
    url = "http://example.com:5000/mcp"
    config = Config(league_manager_url=url)

    assert config.league_manager_url == url


def test_config_set_credentials():
    """
    Test storing credentials after registration.

    Arrange: Create Config
    Act: Call set_credentials
    Assert: All credentials stored correctly
    """
    config = Config()

    config.set_credentials(
        agent_id="P05",
        auth_token="tok_xyz789",
        league_id="L001"
    )

    assert config.agent_id == "P05"
    assert config.auth_token == "tok_xyz789"
    assert config.league_id == "L001"


def test_config_credentials_initially_none():
    """
    Test that credentials are None before registration.

    Arrange: Create Config
    Act: Check auth_token and league_id
    Assert: Both are None
    """
    config = Config()

    assert config.auth_token is None
    assert config.league_id is None


def test_config_set_credentials_updates_agent_id():
    """
    Test that set_credentials updates agent_id.

    Arrange: Create Config with default agent_id
    Act: Call set_credentials with new agent_id
    Assert: agent_id is updated
    """
    config = Config(agent_id="P01")
    assert config.agent_id == "P01"

    config.set_credentials("P10", "token", "league")

    assert config.agent_id == "P10"


def test_config_temp_name_default():
    """
    Test temp_name default value.

    Arrange: Create Config
    Act: Check temp_name
    Assert: Has correct default
    """
    config = Config()

    assert config.temp_name == "player_p01"


def test_config_display_name_default():
    """
    Test display_name default value.

    Arrange: Create Config
    Act: Check display_name
    Assert: Has correct default
    """
    config = Config()

    assert config.display_name == "Agent P01"


def test_config_all_fields_can_be_set():
    """
    Test that all config fields can be set at once.

    Arrange: Prepare all config values
    Act: Create Config with all values
    Assert: All values are set correctly
    """
    config = Config(
        agent_id="P99",
        temp_name="player_p99",
        display_name="Agent P99",
        port=8199,
        league_manager_url="http://test.com/mcp",
        auth_token="test_token",
        league_id="TEST_LEAGUE"
    )

    assert config.agent_id == "P99"
    assert config.temp_name == "player_p99"
    assert config.display_name == "Agent P99"
    assert config.port == 8199
    assert config.league_manager_url == "http://test.com/mcp"
    assert config.auth_token == "test_token"
    assert config.league_id == "TEST_LEAGUE"


@patch.dict(os.environ, {"PLAYER_AGENT_ID": "P50"})
def test_config_loads_from_environment():
    """
    Test that config can load from environment variables.

    Arrange: Set PLAYER_AGENT_ID environment variable
    Act: Create Config
    Assert: agent_id is loaded from env
    """
    config = Config()

    assert config.agent_id == "P50"


@patch.dict(os.environ, {"PLAYER_PORT": "9999"})
def test_config_port_from_environment():
    """
    Test that port can be loaded from environment.

    Arrange: Set PLAYER_PORT environment variable
    Act: Create Config
    Assert: port is loaded from env
    """
    config = Config()

    assert config.port == 9999


def test_config_instance_isolation():
    """
    Test that multiple Config instances are independent.

    Arrange: Create two Config instances
    Act: Modify one instance
    Assert: Other instance unchanged
    """
    config1 = Config(agent_id="P01")
    config2 = Config(agent_id="P02")

    config1.set_credentials("P10", "token1", "league1")

    assert config1.agent_id == "P10"
    assert config2.agent_id == "P02"


def test_config_credentials_can_be_updated():
    """
    Test that credentials can be updated multiple times.

    Arrange: Create Config and set credentials
    Act: Set credentials again with new values
    Assert: Credentials are updated
    """
    config = Config()

    config.set_credentials("P01", "token1", "league1")
    assert config.auth_token == "token1"

    config.set_credentials("P02", "token2", "league2")
    assert config.auth_token == "token2"
    assert config.league_id == "league2"


def test_config_optional_fields_can_be_none():
    """
    Test that optional fields can be None.

    Arrange: Create Config
    Act: Check optional fields
    Assert: Can be None
    """
    config = Config(auth_token=None, league_id=None)

    assert config.auth_token is None
    assert config.league_id is None
