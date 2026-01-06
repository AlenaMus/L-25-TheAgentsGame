"""
Unit tests for MCP message handlers.

Tests:
- register_player handler: Success, rejection, validation
- register_referee handler: Success, rejection, validation
- report_match_result handler: Success, error cases, round completion
"""

import pytest
from datetime import datetime, timezone
from league_manager.handlers.register_player import handle_register_player
from league_manager.handlers.register_referee import handle_register_referee
from league_manager.handlers.report_match_result import handle_match_result_report
from league_manager.registry import RegistryManager
from league_manager.standings import StandingsCalculator
from league_manager.handlers.round_manager import RoundManager


class TestRegisterPlayerHandler:
    """Test player registration handler."""

    @pytest.fixture
    def registry_manager(self):
        """Provide fresh RegistryManager."""
        return RegistryManager(max_players=5)

    @pytest.mark.asyncio
    async def test_register_player_success(self, registry_manager):
        """Test successful player registration."""
        params = {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_REQUEST",
            "sender": "player:alpha",
            "timestamp": "20250115T100000Z",
            "conversation_id": "conv_player_alpha_reg_001",
            "player_meta": {
                "display_name": "Player Alpha",
                "contact_endpoint": "http://localhost:9001/mcp",
                "game_types": ["even_odd"],
                "version": "1.0.0"
            }
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025_even_odd"
        )

        assert response["message_type"] == "LEAGUE_REGISTER_RESPONSE"
        assert response["status"] == "ACCEPTED"
        assert response["player_id"] == "P01"
        assert "auth_token" in response
        assert response["auth_token"].startswith("tok_p")
        assert response["league_id"] == "league_2025_even_odd"
        assert response["conversation_id"] == "conv_player_alpha_reg_001"

    @pytest.mark.asyncio
    async def test_register_player_missing_endpoint(self, registry_manager):
        """Test registration rejection when endpoint is missing."""
        params = {
            "conversation_id": "conv_test",
            "player_meta": {
                "display_name": "Player Alpha"
                # Missing contact_endpoint
            }
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "REJECTED"
        assert "contact_endpoint" in response["reason"]

    @pytest.mark.asyncio
    async def test_register_player_empty_meta(self, registry_manager):
        """Test registration with empty player_meta."""
        params = {
            "conversation_id": "conv_test",
            "player_meta": {}
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_register_player_missing_meta(self, registry_manager):
        """Test registration with missing player_meta."""
        params = {
            "conversation_id": "conv_test"
            # Missing player_meta entirely
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "REJECTED"

    @pytest.mark.asyncio
    async def test_register_player_league_full(self, registry_manager):
        """Test registration rejection when league is full."""
        # Fill up the league (max 5 players)
        for i in range(5):
            await handle_register_player(
                params={
                    "conversation_id": f"conv_{i}",
                    "player_meta": {
                        "display_name": f"Player {i}",
                        "contact_endpoint": f"http://localhost:900{i}/mcp"
                    }
                },
                registry_manager=registry_manager,
                league_id="league_2025"
            )

        # Try to register 6th player
        params = {
            "conversation_id": "conv_overflow",
            "player_meta": {
                "display_name": "Player Overflow",
                "contact_endpoint": "http://localhost:9999/mcp"
            }
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "REJECTED"
        assert "full" in response["reason"].lower()

    @pytest.mark.asyncio
    async def test_register_player_default_values(self, registry_manager):
        """Test that default values are applied correctly."""
        params = {
            "conversation_id": "conv_test",
            "player_meta": {
                "contact_endpoint": "http://localhost:9001/mcp"
                # Missing display_name, game_types, version
            }
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "ACCEPTED"

        # Verify defaults were applied
        player = registry_manager.agent_store.get_player(response["player_id"])
        assert player["display_name"] == "Unknown Player"
        assert player["game_types"] == ["even_odd"]
        assert player["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_register_player_custom_game_types(self, registry_manager):
        """Test registration with custom game types."""
        params = {
            "conversation_id": "conv_test",
            "player_meta": {
                "display_name": "Advanced Player",
                "contact_endpoint": "http://localhost:9001/mcp",
                "game_types": ["even_odd", "rock_paper_scissors"],
                "version": "2.0.0"
            }
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        player = registry_manager.agent_store.get_player(response["player_id"])
        assert player["game_types"] == ["even_odd", "rock_paper_scissors"]
        assert player["version"] == "2.0.0"

    @pytest.mark.asyncio
    async def test_register_player_response_fields(self, registry_manager):
        """Test that response contains all required fields."""
        params = {
            "conversation_id": "conv_test",
            "player_meta": {
                "display_name": "Player Alpha",
                "contact_endpoint": "http://localhost:9001/mcp"
            }
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        # Required fields
        assert "protocol" in response
        assert "message_type" in response
        assert "sender" in response
        assert "timestamp" in response
        assert "conversation_id" in response
        assert "status" in response

        # Success-specific fields
        assert "player_id" in response
        assert "auth_token" in response
        assert "league_id" in response

    @pytest.mark.asyncio
    async def test_register_player_missing_conversation_id(self, registry_manager):
        """Test registration with missing conversation_id."""
        params = {
            "player_meta": {
                "display_name": "Player Alpha",
                "contact_endpoint": "http://localhost:9001/mcp"
            }
            # Missing conversation_id
        }

        response = await handle_register_player(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        # Should still work, using default conversation_id
        assert response["conversation_id"] == "conv_unknown"


class TestRegisterRefereeHandler:
    """Test referee registration handler."""

    @pytest.fixture
    def registry_manager(self):
        """Provide fresh RegistryManager."""
        return RegistryManager(max_referees=3)

    @pytest.mark.asyncio
    async def test_register_referee_success(self, registry_manager):
        """Test successful referee registration."""
        params = {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_REQUEST",
            "sender": "referee:alpha",
            "timestamp": "20250115T100000Z",
            "conversation_id": "conv_ref_alpha_reg_001",
            "referee_meta": {
                "display_name": "Referee Alpha",
                "contact_endpoint": "http://localhost:8001/mcp",
                "max_concurrent_matches": 5,
                "game_types": ["even_odd"],
                "version": "1.0.0"
            }
        }

        response = await handle_register_referee(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025_even_odd"
        )

        assert response["message_type"] == "REFEREE_REGISTER_RESPONSE"
        assert response["status"] == "ACCEPTED"
        assert response["referee_id"] == "REF01"
        assert "auth_token" in response
        assert response["auth_token"].startswith("tok_r")
        assert response["league_id"] == "league_2025_even_odd"

    @pytest.mark.asyncio
    async def test_register_referee_missing_endpoint(self, registry_manager):
        """Test registration rejection when endpoint is missing."""
        params = {
            "conversation_id": "conv_test",
            "referee_meta": {
                "display_name": "Referee Alpha"
                # Missing contact_endpoint
            }
        }

        response = await handle_register_referee(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "REJECTED"
        assert "contact_endpoint" in response["reason"]

    @pytest.mark.asyncio
    async def test_register_referee_max_capacity(self, registry_manager):
        """Test registration rejection when max referees reached."""
        # Register max referees (3)
        for i in range(3):
            await handle_register_referee(
                params={
                    "conversation_id": f"conv_{i}",
                    "referee_meta": {
                        "display_name": f"Referee {i}",
                        "contact_endpoint": f"http://localhost:800{i}/mcp"
                    }
                },
                registry_manager=registry_manager,
                league_id="league_2025"
            )

        # Try to register 4th referee
        params = {
            "conversation_id": "conv_overflow",
            "referee_meta": {
                "display_name": "Referee Overflow",
                "contact_endpoint": "http://localhost:8999/mcp"
            }
        }

        response = await handle_register_referee(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "REJECTED"
        assert "maximum" in response["reason"].lower()

    @pytest.mark.asyncio
    async def test_register_referee_default_values(self, registry_manager):
        """Test that default values are applied correctly."""
        params = {
            "conversation_id": "conv_test",
            "referee_meta": {
                "contact_endpoint": "http://localhost:8001/mcp"
                # Missing display_name, max_concurrent_matches, etc.
            }
        }

        response = await handle_register_referee(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        assert response["status"] == "ACCEPTED"

        # Verify defaults
        referee = registry_manager.agent_store.get_referee(response["referee_id"])
        assert referee["display_name"] == "Unknown Referee"
        assert referee["max_concurrent_matches"] == 2
        assert referee["game_types"] == ["even_odd"]
        assert referee["version"] == "1.0.0"

    @pytest.mark.asyncio
    async def test_register_referee_custom_concurrent_matches(self, registry_manager):
        """Test registration with custom concurrent match limit."""
        params = {
            "conversation_id": "conv_test",
            "referee_meta": {
                "display_name": "Super Referee",
                "contact_endpoint": "http://localhost:8001/mcp",
                "max_concurrent_matches": 10
            }
        }

        response = await handle_register_referee(
            params=params,
            registry_manager=registry_manager,
            league_id="league_2025"
        )

        referee = registry_manager.agent_store.get_referee(response["referee_id"])
        assert referee["max_concurrent_matches"] == 10

    @pytest.mark.asyncio
    async def test_register_referee_sequential_ids(self, registry_manager):
        """Test that referee IDs are assigned sequentially."""
        responses = []

        for i in range(3):
            response = await handle_register_referee(
                params={
                    "conversation_id": f"conv_{i}",
                    "referee_meta": {
                        "display_name": f"Referee {i}",
                        "contact_endpoint": f"http://localhost:800{i}/mcp"
                    }
                },
                registry_manager=registry_manager,
                league_id="league_2025"
            )
            responses.append(response)

        assert responses[0]["referee_id"] == "REF01"
        assert responses[1]["referee_id"] == "REF02"
        assert responses[2]["referee_id"] == "REF03"


class TestReportMatchResultHandler:
    """Test match result reporting handler."""

    @pytest.fixture
    def standings_calculator(self):
        """Provide StandingsCalculator."""
        return StandingsCalculator()

    @pytest.fixture
    def round_manager(self):
        """Provide RoundManager."""
        return RoundManager()

    @pytest.fixture
    def setup_round(self, round_manager):
        """Setup a round with matches."""
        round_manager.start_round(
            round_id=1,
            matches=[
                {"match_id": "R1M1", "player_a": "P01", "player_b": "P02"},
                {"match_id": "R1M2", "player_a": "P03", "player_b": "P04"}
            ]
        )
        return round_manager

    @pytest.mark.asyncio
    async def test_report_match_result_win(self, standings_calculator, round_manager):
        """Test reporting a match result with a winner."""
        # Setup round
        round_manager.start_round(
            round_id=1,
            matches=[{"match_id": "R1M1", "player_a": "P01", "player_b": "P02"}]
        )

        params = {
            "protocol": "league.v2",
            "message_type": "MATCH_RESULT_REPORT",
            "sender": "referee:REF01",
            "timestamp": "2025-01-15T10:30:00Z",
            "conversation_id": "conv_match_r1m1_result",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0},
                "details": {
                    "drawn_number": 8,
                    "choices": {"P01": "even", "P02": "odd"}
                }
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025_even_odd"
        )

        assert response["message_type"] == "MATCH_RESULT_ACK"
        assert response["acknowledged"] is True
        assert response["match_id"] == "R1M1"
        assert "round_complete" in response

    @pytest.mark.asyncio
    async def test_report_match_result_tie(self, standings_calculator, round_manager):
        """Test reporting a match result with a tie."""
        round_manager.start_round(
            round_id=1,
            matches=[{"match_id": "R1M1", "player_a": "P01", "player_b": "P02"}]
        )

        params = {
            "conversation_id": "conv_test",
            "round_id": 1,
            "match_id": "R1M1",
            "result": {
                "winner": None,  # Tie
                "score": {"P01": 1, "P02": 1}
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert response["acknowledged"] is True

    @pytest.mark.asyncio
    async def test_report_match_result_missing_match_id(self, standings_calculator, round_manager):
        """Test error handling for missing match_id."""
        params = {
            "conversation_id": "conv_test",
            "round_id": 1,
            # Missing match_id
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0}
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert response["acknowledged"] is False
        assert "error" in response

    @pytest.mark.asyncio
    async def test_report_match_result_missing_round_id(self, standings_calculator, round_manager):
        """Test error handling for missing round_id."""
        params = {
            "conversation_id": "conv_test",
            "match_id": "R1M1",
            # Missing round_id
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0}
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert response["acknowledged"] is False
        assert "error" in response

    @pytest.mark.asyncio
    async def test_report_match_result_invalid_score(self, standings_calculator, round_manager):
        """Test error handling for invalid score (not exactly 2 players)."""
        params = {
            "conversation_id": "conv_test",
            "round_id": 1,
            "match_id": "R1M1",
            "result": {
                "winner": "P01",
                "score": {"P01": 3}  # Only one player
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert response["acknowledged"] is False
        assert "error" in response
        assert "2 players" in response["error"]

    @pytest.mark.asyncio
    async def test_report_match_result_updates_standings(self, standings_calculator, round_manager):
        """Test that standings are updated correctly."""
        round_manager.start_round(
            round_id=1,
            matches=[{"match_id": "R1M1", "player_a": "P01", "player_b": "P02"}]
        )

        params = {
            "conversation_id": "conv_test",
            "round_id": 1,
            "match_id": "R1M1",
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0}
            }
        }

        await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        # Verify standings were updated
        standings = standings_calculator.get_current_standings()
        p01_standing = next((s for s in standings if s["player_id"] == "P01"), None)
        p02_standing = next((s for s in standings if s["player_id"] == "P02"), None)

        assert p01_standing is not None
        assert p01_standing["wins"] == 1
        assert p01_standing["points"] == 3

        assert p02_standing is not None
        assert p02_standing["losses"] == 1
        assert p02_standing["points"] == 0

    @pytest.mark.asyncio
    async def test_report_match_result_round_completion(self, standings_calculator, setup_round):
        """Test round completion detection."""
        round_manager = setup_round

        # Report first match
        await handle_match_result_report(
            params={
                "conversation_id": "conv1",
                "round_id": 1,
                "match_id": "R1M1",
                "result": {"winner": "P01", "score": {"P01": 3, "P02": 0}}
            },
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        # Report second match - should complete the round
        response = await handle_match_result_report(
            params={
                "conversation_id": "conv2",
                "round_id": 1,
                "match_id": "R1M2",
                "result": {"winner": "P03", "score": {"P03": 3, "P04": 0}}
            },
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert response["round_complete"] is True

    @pytest.mark.asyncio
    async def test_report_match_result_response_fields(self, standings_calculator, round_manager):
        """Test that response contains all required fields."""
        round_manager.start_round(
            round_id=1,
            matches=[{"match_id": "R1M1", "player_a": "P01", "player_b": "P02"}]
        )

        params = {
            "conversation_id": "conv_test",
            "round_id": 1,
            "match_id": "R1M1",
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0}
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert "protocol" in response
        assert "message_type" in response
        assert "sender" in response
        assert "timestamp" in response
        assert "conversation_id" in response
        assert "acknowledged" in response
        assert "match_id" in response
        assert "round_complete" in response

    @pytest.mark.asyncio
    async def test_report_match_result_empty_score(self, standings_calculator, round_manager):
        """Test error handling for empty score."""
        params = {
            "conversation_id": "conv_test",
            "round_id": 1,
            "match_id": "R1M1",
            "result": {
                "winner": "P01",
                "score": {}  # Empty score
            }
        }

        response = await handle_match_result_report(
            params=params,
            standings_calculator=standings_calculator,
            round_manager=round_manager,
            league_id="league_2025"
        )

        assert response["acknowledged"] is False
        assert "error" in response
