"""
Integration Test: Player Registration with League Manager.

Tests Task 26 - Player agents can successfully register with the
League Manager and receive proper credentials.
"""

import pytest
from tests.integration.utils import MCPClient


@pytest.mark.asyncio
async def test_player_registration_success(league_manager, player):
    """
    Test successful player registration.

    Scenario:
        1. Player sends registration request to League Manager
        2. League Manager validates request
        3. League Manager assigns player ID
        4. League Manager returns credentials

    Expected:
        - Registration accepted
        - Player receives valid player_id
        - Player receives auth_token
        - Player receives league_id
    """
    async with MCPClient() as client:
        # Send registration request
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-reg-001",
                "player_meta": {
                    "display_name": "TestPlayer1",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player.endpoint
                }
            }
        )

        # Verify response structure
        assert "result" in response
        result = response["result"]

        # Verify registration accepted
        assert result["status"] == "ACCEPTED"

        # Verify player received credentials
        assert "player_id" in result
        assert result["player_id"].startswith("P")

        assert "auth_token" in result
        assert len(result["auth_token"]) > 0

        assert "league_id" in result
        assert len(result["league_id"]) > 0


@pytest.mark.asyncio
async def test_multiple_player_registration(league_manager, two_players):
    """
    Test multiple players can register.

    Scenario:
        1. First player registers
        2. Second player registers
        3. Both receive unique player IDs

    Expected:
        - Both registrations succeed
        - Player IDs are unique
        - Both receive auth tokens
    """
    player1, player2 = two_players

    async with MCPClient() as client:
        # Register player 1
        response1 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-reg-p1",
                "player_meta": {
                    "display_name": "Player1",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player1.endpoint
                }
            }
        )

        # Register player 2
        response2 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:01Z",
                "conversation_id": "test-reg-p2",
                "player_meta": {
                    "display_name": "Player2",
                    "version": "1.0.0",
                    "strategy": "adaptive",
                    "contact_endpoint": player2.endpoint
                }
            }
        )

        # Verify both succeeded
        assert response1["result"]["status"] == "ACCEPTED"
        assert response2["result"]["status"] == "ACCEPTED"

        # Verify unique player IDs
        player1_id = response1["result"]["player_id"]
        player2_id = response2["result"]["player_id"]
        assert player1_id != player2_id

        # Verify both start with 'P'
        assert player1_id.startswith("P")
        assert player2_id.startswith("P")


@pytest.mark.asyncio
async def test_player_registration_duplicate_endpoint(league_manager, player):
    """
    Test registration with duplicate endpoint.

    Scenario:
        1. Player registers successfully
        2. Same player tries to register again with same endpoint
        3. League Manager should handle gracefully

    Expected:
        - First registration succeeds
        - Second registration either:
          a) Returns same player_id (idempotent), OR
          b) Rejects with appropriate error
    """
    async with MCPClient() as client:
        # First registration
        response1 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-dup-001",
                "player_meta": {
                    "display_name": "DuplicatePlayer",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player.endpoint
                }
            }
        )

        assert response1["result"]["status"] == "ACCEPTED"
        first_player_id = response1["result"]["player_id"]

        # Second registration with same endpoint
        response2 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:unregistered",
                "timestamp": "2025-12-24T10:00:05Z",
                "conversation_id": "test-dup-002",
                "player_meta": {
                    "display_name": "DuplicatePlayer",
                    "version": "1.0.0",
                    "strategy": "random",
                    "contact_endpoint": player.endpoint
                }
            }
        )

        # Either same ID (idempotent) or rejected
        if response2["result"]["status"] == "ACCEPTED":
            assert response2["result"]["player_id"] == first_player_id
        else:
            assert response2["result"]["status"] == "REJECTED"


@pytest.mark.asyncio
async def test_player_registration_invalid_request(league_manager):
    """
    Test registration with invalid/missing fields.

    Scenario:
        1. Send registration with missing required fields
        2. League Manager validates and rejects

    Expected:
        - Registration rejected
        - Error message indicates validation failure
    """
    async with MCPClient() as client:
        # Missing player_meta
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                "sender": "player:invalid",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-invalid-001"
                # Missing player_meta
            }
        )

        # Should be rejected or return error
        if "result" in response:
            assert response["result"]["status"] == "REJECTED"
        elif "error" in response:
            assert response["error"] is not None
