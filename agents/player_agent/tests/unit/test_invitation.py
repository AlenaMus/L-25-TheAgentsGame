"""
Unit tests for handle_game_invitation handler.

Tests the game invitation acceptance logic including:
- Valid invitation responses
- Message envelope formatting
- Required field handling
- Logging behavior
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from player_agent.handlers.invitation import handle_game_invitation


@pytest.mark.asyncio
async def test_handle_game_invitation_valid_params_returns_acceptance():
    """
    Test that valid invitation params return acceptance response.

    Arrange: Create valid GAME_INVITATION params
    Act: Call handle_game_invitation
    Assert: Response contains accept=True and all required fields
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02",
        "league_id": "L001",
        "round_id": "R1",
        "game_type": "even_odd",
        "role_in_match": "PLAYER_A"
    }

    result = await handle_game_invitation(params)

    assert result["accept"] is True
    assert result["match_id"] == "R1M1"
    assert result["conversation_id"] == "convr1m1001"


@pytest.mark.asyncio
async def test_handle_game_invitation_contains_league_v2_protocol():
    """
    Test that response follows league.v2 protocol format.

    Arrange: Create valid invitation params
    Act: Call handle_game_invitation
    Assert: Response has protocol="league.v2"
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert result["protocol"] == "league.v2"


@pytest.mark.asyncio
async def test_handle_game_invitation_has_correct_message_type():
    """
    Test that response has correct message_type.

    Arrange: Create valid invitation params
    Act: Call handle_game_invitation
    Assert: Response has message_type="GAME_JOIN_ACK"
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert result["message_type"] == "GAME_JOIN_ACK"


@pytest.mark.asyncio
async def test_handle_game_invitation_sender_format():
    """
    Test that sender field follows player:<id> format.

    Arrange: Create valid invitation params
    Act: Call handle_game_invitation
    Assert: Sender follows "player:P01" format
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02",
        "player_id": "P01"
    }

    result = await handle_game_invitation(params)

    assert result["sender"] == "player:P01"
    assert result["sender"].startswith("player:")


@pytest.mark.asyncio
async def test_handle_game_invitation_timestamp_is_utc():
    """
    Test that timestamp is in UTC format.

    Arrange: Create valid invitation params
    Act: Call handle_game_invitation
    Assert: Timestamp ends with 'Z' and is valid UTC
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert result["timestamp"].endswith("Z")
    assert "arrival_timestamp" in result
    assert result["arrival_timestamp"].endswith("Z")

    # Verify timestamp can be parsed
    timestamp = result["timestamp"].replace("Z", "+00:00")
    dt = datetime.fromisoformat(timestamp)
    assert dt.tzinfo is not None


@pytest.mark.asyncio
async def test_handle_game_invitation_includes_auth_token():
    """
    Test that response includes auth_token.

    Arrange: Create valid invitation params
    Act: Call handle_game_invitation
    Assert: auth_token field is present
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert "auth_token" in result
    assert isinstance(result["auth_token"], str)


@pytest.mark.asyncio
async def test_handle_game_invitation_includes_player_id():
    """
    Test that response includes player_id.

    Arrange: Create valid invitation params
    Act: Call handle_game_invitation
    Assert: player_id field is present
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert "player_id" in result
    assert result["player_id"] is not None


@pytest.mark.asyncio
async def test_handle_game_invitation_logs_received():
    """
    Test that invitation receipt is logged.

    Arrange: Mock logger, create valid params
    Act: Call handle_game_invitation
    Assert: Logger.info called with invitation received message
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02",
        "round_id": "R1"
    }

    with patch("player_agent.handlers.invitation.logger") as mock_logger:
        await handle_game_invitation(params)

        # Verify logging was called
        assert mock_logger.info.call_count >= 2  # Received + Accepted

        # Check first call (received)
        first_call_args = mock_logger.info.call_args_list[0]
        assert "invitation" in first_call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handle_game_invitation_logs_acceptance():
    """
    Test that invitation acceptance is logged.

    Arrange: Mock logger, create valid params
    Act: Call handle_game_invitation
    Assert: Logger.info called with acceptance message
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    with patch("player_agent.handlers.invitation.logger") as mock_logger:
        await handle_game_invitation(params)

        # Check second call (accepted)
        second_call_args = mock_logger.info.call_args_list[1]
        assert "accept" in second_call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handle_game_invitation_minimal_params():
    """
    Test handling invitation with only required params.

    Arrange: Create params with only required fields
    Act: Call handle_game_invitation
    Assert: Response is valid and accepts invitation
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1"
    }

    result = await handle_game_invitation(params)

    assert result["accept"] is True
    assert result["conversation_id"] == "convr1m1001"
    assert result["match_id"] == "R1M1"


@pytest.mark.asyncio
async def test_handle_game_invitation_preserves_conversation_id():
    """
    Test that conversation_id is preserved from request to response.

    Arrange: Create params with specific conversation_id
    Act: Call handle_game_invitation
    Assert: Response has same conversation_id
    """
    conversation_id = "custom_conv_12345"
    params = {
        "conversation_id": conversation_id,
        "match_id": "R1M1",
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert result["conversation_id"] == conversation_id


@pytest.mark.asyncio
async def test_handle_game_invitation_preserves_match_id():
    """
    Test that match_id is preserved from request to response.

    Arrange: Create params with specific match_id
    Act: Call handle_game_invitation
    Assert: Response has same match_id
    """
    match_id = "CUSTOM_MATCH_999"
    params = {
        "conversation_id": "convr1m1001",
        "match_id": match_id,
        "opponent_id": "P02"
    }

    result = await handle_game_invitation(params)

    assert result["match_id"] == match_id


@pytest.mark.asyncio
async def test_handle_game_invitation_always_accepts():
    """
    Test that handler always accepts invitations (Phase 1 requirement).

    Arrange: Create multiple different invitation params
    Act: Call handle_game_invitation multiple times
    Assert: All responses have accept=True
    """
    test_cases = [
        {"conversation_id": "conv1", "match_id": "M1", "opponent_id": "P02"},
        {"conversation_id": "conv2", "match_id": "M2", "opponent_id": "P03"},
        {"conversation_id": "conv3", "match_id": "M3", "opponent_id": "P04"}
    ]

    for params in test_cases:
        result = await handle_game_invitation(params)
        assert result["accept"] is True
