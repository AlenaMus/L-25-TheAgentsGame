"""
Unit tests for choose_parity handler.

Tests the parity choice logic including:
- RandomStrategy integration
- Valid choice generation ("even" or "odd")
- Message envelope formatting
- Context handling
- Error recovery and validation
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from player_agent.handlers.choice import choose_parity


@pytest.mark.asyncio
async def test_choose_parity_returns_valid_choice():
    """
    Test that choose_parity returns either "even" or "odd".

    Arrange: Create valid CHOOSE_PARITY_CALL params
    Act: Call choose_parity
    Assert: parity_choice is "even" or "odd"
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_type": "even_odd",
        "context": {
            "opponent_id": "P02"
        }
    }

    result = await choose_parity(params)

    assert result["parity_choice"] in ["even", "odd"]


@pytest.mark.asyncio
async def test_choose_parity_follows_league_v2_protocol():
    """
    Test that response follows league.v2 protocol format.

    Arrange: Create valid choice params
    Act: Call choose_parity
    Assert: Response has protocol="league.v2"
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["protocol"] == "league.v2"


@pytest.mark.asyncio
async def test_choose_parity_has_correct_message_type():
    """
    Test that response has correct message_type.

    Arrange: Create valid choice params
    Act: Call choose_parity
    Assert: Response has message_type="CHOOSE_PARITY_RESPONSE"
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["message_type"] == "CHOOSE_PARITY_RESPONSE"


@pytest.mark.asyncio
async def test_choose_parity_sender_format():
    """
    Test that sender field follows player:<id> format.

    Arrange: Create valid choice params
    Act: Call choose_parity
    Assert: Sender follows "player:P01" format
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["sender"] == "player:P01"
    assert result["sender"].startswith("player:")


@pytest.mark.asyncio
async def test_choose_parity_timestamp_is_utc():
    """
    Test that timestamp is in UTC format.

    Arrange: Create valid choice params
    Act: Call choose_parity
    Assert: Timestamp ends with 'Z' and is valid UTC
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["timestamp"].endswith("Z")

    # Verify timestamp can be parsed
    timestamp = result["timestamp"].replace("Z", "+00:00")
    dt = datetime.fromisoformat(timestamp)
    assert dt.tzinfo is not None


@pytest.mark.asyncio
async def test_choose_parity_includes_auth_token():
    """
    Test that response includes auth_token.

    Arrange: Create valid choice params
    Act: Call choose_parity
    Assert: auth_token field is present
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert "auth_token" in result
    assert isinstance(result["auth_token"], str)


@pytest.mark.asyncio
async def test_choose_parity_preserves_conversation_id():
    """
    Test that conversation_id is preserved from request to response.

    Arrange: Create params with specific conversation_id
    Act: Call choose_parity
    Assert: Response has same conversation_id
    """
    conversation_id = "custom_conv_98765"
    params = {
        "conversation_id": conversation_id,
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["conversation_id"] == conversation_id


@pytest.mark.asyncio
async def test_choose_parity_preserves_match_id():
    """
    Test that match_id is preserved from request to response.

    Arrange: Create params with specific match_id
    Act: Call choose_parity
    Assert: Response has same match_id
    """
    match_id = "CUSTOM_R5M7"
    params = {
        "conversation_id": "convr1m1001",
        "match_id": match_id,
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["match_id"] == match_id


@pytest.mark.asyncio
async def test_choose_parity_preserves_player_id():
    """
    Test that player_id is preserved from request to response.

    Arrange: Create params with specific player_id
    Act: Call choose_parity
    Assert: Response has same player_id
    """
    player_id = "P01"
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": player_id,
        "context": {"opponent_id": "P02"}
    }

    result = await choose_parity(params)

    assert result["player_id"] == player_id


@pytest.mark.asyncio
async def test_choose_parity_uses_random_strategy():
    """
    Test that RandomStrategy is instantiated and used.

    Arrange: Mock RandomStrategy, create valid params
    Act: Call choose_parity
    Assert: RandomStrategy.choose_parity was called
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    with patch("player_agent.handlers.choice.RandomStrategy") as MockStrategy:
        mock_instance = MagicMock()
        mock_instance.choose_parity.return_value = "even"
        mock_instance.get_name.return_value = "RandomStrategy"
        MockStrategy.return_value = mock_instance

        result = await choose_parity(params)

        # Verify strategy was instantiated and used
        MockStrategy.assert_called_once()
        mock_instance.choose_parity.assert_called_once()


@pytest.mark.asyncio
async def test_choose_parity_strategy_receives_match_id():
    """
    Test that strategy receives correct match_id parameter.

    Arrange: Mock RandomStrategy, create params
    Act: Call choose_parity
    Assert: Strategy called with match_id
    """
    match_id = "TEST_MATCH_123"
    params = {
        "conversation_id": "convr1m1001",
        "match_id": match_id,
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    with patch("player_agent.handlers.choice.RandomStrategy") as MockStrategy:
        mock_instance = MagicMock()
        mock_instance.choose_parity.return_value = "odd"
        mock_instance.get_name.return_value = "RandomStrategy"
        MockStrategy.return_value = mock_instance

        await choose_parity(params)

        # Check strategy was called with match_id
        call_kwargs = mock_instance.choose_parity.call_args.kwargs
        assert call_kwargs["match_id"] == match_id


@pytest.mark.asyncio
async def test_choose_parity_strategy_receives_opponent_id():
    """
    Test that strategy receives opponent_id from context.

    Arrange: Mock RandomStrategy, create params with opponent_id
    Act: Call choose_parity
    Assert: Strategy called with opponent_id
    """
    opponent_id = "P99"
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": opponent_id}
    }

    with patch("player_agent.handlers.choice.RandomStrategy") as MockStrategy:
        mock_instance = MagicMock()
        mock_instance.choose_parity.return_value = "even"
        mock_instance.get_name.return_value = "RandomStrategy"
        MockStrategy.return_value = mock_instance

        await choose_parity(params)

        # Check strategy was called with opponent_id
        call_kwargs = mock_instance.choose_parity.call_args.kwargs
        assert call_kwargs["opponent_id"] == opponent_id


@pytest.mark.asyncio
async def test_choose_parity_handles_missing_opponent_id():
    """
    Test graceful handling when opponent_id is missing from context.

    Arrange: Create params without opponent_id in context
    Act: Call choose_parity
    Assert: Function completes without error, uses default
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {}  # Empty context
    }

    result = await choose_parity(params)

    assert result["parity_choice"] in ["even", "odd"]


@pytest.mark.asyncio
async def test_choose_parity_validates_invalid_choice():
    """
    Test that invalid choices from strategy are caught and corrected.

    Arrange: Mock strategy to return invalid choice
    Act: Call choose_parity
    Assert: Response has valid choice ("even" as fallback)
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    with patch("player_agent.handlers.choice.RandomStrategy") as MockStrategy:
        mock_instance = MagicMock()
        mock_instance.choose_parity.return_value = "INVALID"  # Invalid choice
        mock_instance.get_name.return_value = "RandomStrategy"
        MockStrategy.return_value = mock_instance

        result = await choose_parity(params)

        # Should default to "even" when invalid
        assert result["parity_choice"] == "even"


@pytest.mark.asyncio
async def test_choose_parity_logs_request():
    """
    Test that choice request is logged.

    Arrange: Mock logger, create valid params
    Act: Call choose_parity
    Assert: Logger.info called with request message
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    with patch("player_agent.handlers.choice.logger") as mock_logger:
        await choose_parity(params)

        # Verify logging was called (request + choice made)
        assert mock_logger.info.call_count >= 2


@pytest.mark.asyncio
async def test_choose_parity_logs_choice_made():
    """
    Test that final choice is logged.

    Arrange: Mock logger, create valid params
    Act: Call choose_parity
    Assert: Logger.info called with choice information
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    with patch("player_agent.handlers.choice.logger") as mock_logger:
        await choose_parity(params)

        # Check that choice was logged
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any("choice" in str(call).lower() for call in log_calls)


@pytest.mark.asyncio
async def test_choose_parity_logs_error_on_invalid_choice():
    """
    Test that logger.error is called when strategy returns invalid choice.

    Arrange: Mock strategy to return invalid choice, mock logger
    Act: Call choose_parity
    Assert: Logger.error called
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    with patch("player_agent.handlers.choice.RandomStrategy") as MockStrategy:
        mock_instance = MagicMock()
        mock_instance.choose_parity.return_value = "INVALID"
        mock_instance.get_name.return_value = "RandomStrategy"
        MockStrategy.return_value = mock_instance

        with patch("player_agent.handlers.choice.logger") as mock_logger:
            await choose_parity(params)

            # Verify error was logged
            mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_choose_parity_handles_empty_context():
    """
    Test handling when context is completely missing.

    Arrange: Create params without context field
    Act: Call choose_parity
    Assert: Function completes successfully
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01"
        # No context field
    }

    result = await choose_parity(params)

    assert result["parity_choice"] in ["even", "odd"]
    assert result["conversation_id"] == "convr1m1001"


@pytest.mark.asyncio
async def test_choose_parity_statistical_distribution():
    """
    Test that RandomStrategy produces roughly 50/50 distribution.

    Arrange: Create params
    Act: Call choose_parity multiple times
    Assert: Distribution is roughly 50/50 (within reasonable bounds)
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "context": {"opponent_id": "P02"}
    }

    choices = []
    for i in range(100):
        params["match_id"] = f"R1M{i}"
        result = await choose_parity(params)
        choices.append(result["parity_choice"])

    even_count = choices.count("even")
    odd_count = choices.count("odd")

    # With 100 samples, expect 30-70 range (very loose bounds)
    assert 30 <= even_count <= 70
    assert 30 <= odd_count <= 70
    assert even_count + odd_count == 100
