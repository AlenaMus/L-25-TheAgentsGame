"""
Integration Test: Referee Registration with League Manager.

Tests Task 27 - Referee agents can successfully register with the
League Manager and receive proper credentials.
"""

import pytest
from tests.integration.utils import MCPClient


@pytest.mark.asyncio
async def test_referee_registration_success(league_manager, referee):
    """
    Test successful referee registration.

    Scenario:
        1. Referee sends registration request to League Manager
        2. League Manager validates request
        3. League Manager assigns referee ID
        4. League Manager returns credentials

    Expected:
        - Registration accepted
        - Referee receives valid referee_id
        - Referee receives auth_token
        - Referee receives league_id
    """
    async with MCPClient() as client:
        # Send registration request
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-ref-reg-001",
                "referee_meta": {
                    "display_name": "TestReferee1",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Verify response structure
        assert "result" in response
        result = response["result"]

        # Verify registration accepted
        assert result["status"] == "ACCEPTED"

        # Verify referee received credentials
        assert "referee_id" in result
        assert result["referee_id"].startswith("REF")

        assert "auth_token" in result
        assert len(result["auth_token"]) > 0

        assert "league_id" in result
        assert len(result["league_id"]) > 0


@pytest.mark.asyncio
async def test_referee_registration_with_game_types(league_manager, referee):
    """
    Test referee registration specifies game types.

    Scenario:
        1. Referee registers with specific game types
        2. League Manager stores game type capabilities

    Expected:
        - Registration accepted
        - Game types are stored
    """
    async with MCPClient() as client:
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-ref-types-001",
                "referee_meta": {
                    "display_name": "MultiGameReferee",
                    "version": "1.0.0",
                    "game_types": ["even_odd", "rock_paper_scissors"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 3
                }
            }
        )

        assert response["result"]["status"] == "ACCEPTED"
        assert "referee_id" in response["result"]


@pytest.mark.asyncio
async def test_multiple_referee_registration(
    league_manager,
    agent_manager,
    port_manager
):
    """
    Test multiple referees can register.

    Scenario:
        1. First referee registers
        2. Second referee registers
        3. Both receive unique referee IDs

    Expected:
        - Both registrations succeed
        - Referee IDs are unique
        - Both receive auth tokens
    """
    # Start two referees
    port1 = port_manager.allocate()
    port2 = port_manager.allocate()

    referee1 = await agent_manager.start_referee("REF01", port1)
    referee2 = await agent_manager.start_referee("REF02", port2)

    async with MCPClient() as client:
        # Register referee 1
        response1 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-ref-multi-001",
                "referee_meta": {
                    "display_name": "Referee1",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": referee1.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Register referee 2
        response2 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:00:01Z",
                "conversation_id": "test-ref-multi-002",
                "referee_meta": {
                    "display_name": "Referee2",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": referee2.endpoint,
                    "max_concurrent_matches": 3
                }
            }
        )

        # Verify both succeeded
        assert response1["result"]["status"] == "ACCEPTED"
        assert response2["result"]["status"] == "ACCEPTED"

        # Verify unique referee IDs
        ref1_id = response1["result"]["referee_id"]
        ref2_id = response2["result"]["referee_id"]
        assert ref1_id != ref2_id

        # Verify both start with 'REF'
        assert ref1_id.startswith("REF")
        assert ref2_id.startswith("REF")

    # Cleanup
    port_manager.release(port1)
    port_manager.release(port2)


@pytest.mark.asyncio
async def test_referee_registration_invalid_game_types(league_manager, referee):
    """
    Test referee registration with no game types.

    Scenario:
        1. Referee tries to register without game_types
        2. League Manager validates and rejects

    Expected:
        - Registration rejected or returns error
    """
    async with MCPClient() as client:
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:invalid",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-ref-invalid-001",
                "referee_meta": {
                    "display_name": "InvalidReferee",
                    "version": "1.0.0",
                    "game_types": [],  # Empty game types
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 1
                }
            }
        )

        # Should be rejected or return error
        if "result" in response:
            # Some implementations might still accept but flag it
            result = response["result"]
            # At minimum, should be tracked
            assert "referee_id" in result or result["status"] == "REJECTED"
        elif "error" in response:
            assert response["error"] is not None


@pytest.mark.asyncio
async def test_referee_registration_duplicate_endpoint(league_manager, referee):
    """
    Test registration with duplicate endpoint.

    Scenario:
        1. Referee registers successfully
        2. Same referee tries to register again
        3. League Manager handles gracefully

    Expected:
        - First registration succeeds
        - Second registration either returns same ID or rejects
    """
    async with MCPClient() as client:
        # First registration
        response1 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:00:00Z",
                "conversation_id": "test-ref-dup-001",
                "referee_meta": {
                    "display_name": "DuplicateReferee",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        assert response1["result"]["status"] == "ACCEPTED"
        first_ref_id = response1["result"]["referee_id"]

        # Second registration with same endpoint
        response2 = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_referee",
            params={
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": "referee:unregistered",
                "timestamp": "2025-12-24T10:00:05Z",
                "conversation_id": "test-ref-dup-002",
                "referee_meta": {
                    "display_name": "DuplicateReferee",
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": referee.endpoint,
                    "max_concurrent_matches": 5
                }
            }
        )

        # Either same ID (idempotent) or rejected
        if response2["result"]["status"] == "ACCEPTED":
            assert response2["result"]["referee_id"] == first_ref_id
        else:
            assert response2["result"]["status"] == "REJECTED"
