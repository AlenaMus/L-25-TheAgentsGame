"""
Integration tests for registration flow.
"""

import pytest
from league_manager.handlers.player_registration import register_player
from league_manager.handlers.referee_registration import register_referee


@pytest.mark.asyncio
async def test_player_registration(agent_registry, standings_calc):
    """Test complete player registration flow."""
    params = {
        "player_meta": {
            "display_name": "Test Player",
            "contact_endpoint": "http://localhost:8101/mcp",
            "game_types": ["even_odd"],
            "version": "1.0.0"
        }
    }
    
    result = await register_player(params, agent_registry, standings_calc)
    
    assert result["status"] == "ACCEPTED"
    assert result["player_id"] == "P01"
    assert "auth_token" in result
    assert agent_registry.player_count() == 1


@pytest.mark.asyncio
async def test_referee_registration(agent_registry):
    """Test complete referee registration flow."""
    params = {
        "referee_meta": {
            "display_name": "Test Referee",
            "contact_endpoint": "http://localhost:8001/mcp",
            "supported_games": ["even_odd"],
            "max_concurrent_games": 5,
            "version": "1.0.0"
        }
    }
    
    result = await register_referee(params, agent_registry)
    
    assert result["status"] == "ACCEPTED"
    assert result["referee_id"] == "REF01"
    assert "auth_token" in result
    assert agent_registry.referee_count() == 1


@pytest.mark.asyncio
async def test_multiple_player_registration(agent_registry, standings_calc):
    """Test registering multiple players."""
    for i in range(3):
        params = {
            "player_meta": {
                "display_name": f"Player {i+1}",
                "contact_endpoint": f"http://localhost:810{i+1}/mcp",
                "game_types": ["even_odd"],
                "version": "1.0.0"
            }
        }
        result = await register_player(params, agent_registry, standings_calc)
        assert result["status"] == "ACCEPTED"
        assert result["player_id"] == f"P{i+1:02d}"
    
    assert agent_registry.player_count() == 3
