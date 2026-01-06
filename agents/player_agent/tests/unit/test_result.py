"""
Unit tests for notify_match_result handler.

Tests the match result notification handling including:
- Result acknowledgment
- Game result parsing
- Opponent choice extraction
- Logging behavior
"""

import pytest
from unittest.mock import patch, MagicMock

from player_agent.handlers.result import notify_match_result


@pytest.mark.asyncio
async def test_notify_match_result_returns_acknowledgment():
    """
    Test that handler returns acknowledgment.

    Arrange: Create valid GAME_OVER params
    Act: Call notify_match_result
    Assert: Response contains acknowledged=True
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_type": "even_odd",
        "game_result": {
            "status": "WIN",
            "winner_player_id": "P01",
            "drawn_number": 8,
            "number_parity": "even",
            "choices": {
                "P01": "even",
                "P02": "odd"
            },
            "reason": "P01 chose even, number was even"
        }
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_handles_win():
    """
    Test handling of win result.

    Arrange: Create WIN game_result
    Act: Call notify_match_result
    Assert: Acknowledgment returned without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "status": "WIN",
            "winner_player_id": "P01",
            "drawn_number": 5
        }
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_handles_loss():
    """
    Test handling of loss result.

    Arrange: Create LOSS game_result
    Act: Call notify_match_result
    Assert: Acknowledgment returned without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "status": "LOSS",
            "winner_player_id": "P02",
            "drawn_number": 3
        }
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_handles_draw():
    """
    Test handling of draw result.

    Arrange: Create DRAW game_result with null winner
    Act: Call notify_match_result
    Assert: Acknowledgment returned without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "status": "DRAW",
            "winner_player_id": None,
            "drawn_number": 7
        }
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_extracts_opponent_id():
    """
    Test that opponent_id is extracted from choices.

    Arrange: Create game_result with choices dict
    Act: Call notify_match_result with mocked logger
    Assert: Logger called with opponent_id information
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "winner_player_id": "P02",
            "drawn_number": 4,
            "choices": {
                "P01": "odd",
                "P02": "even"
            }
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Check that opponent_id was logged
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        # Opponent ID should appear in logs
        assert any("P02" in str(call) for call in log_calls)


@pytest.mark.asyncio
async def test_notify_match_result_extracts_player_choice():
    """
    Test that player's own choice is extracted.

    Arrange: Create game_result with choices
    Act: Call notify_match_result with mocked logger
    Assert: Logger called with my_choice information
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "winner_player_id": "P01",
            "drawn_number": 6,
            "choices": {
                "P01": "even",
                "P02": "odd"
            }
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Player's choice should be in logs
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        # "even" should appear in logs
        assert any("even" in str(call).lower() for call in log_calls)


@pytest.mark.asyncio
async def test_notify_match_result_extracts_opponent_choice():
    """
    Test that opponent's choice is extracted.

    Arrange: Create game_result with both player choices
    Act: Call notify_match_result with mocked logger
    Assert: Both choices are logged
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "winner_player_id": "P02",
            "drawn_number": 7,
            "choices": {
                "P01": "even",
                "P02": "odd"
            }
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Both even and odd should appear
        log_calls = str(mock_logger.info.call_args_list)
        assert "even" in log_calls.lower()
        assert "odd" in log_calls.lower()


@pytest.mark.asyncio
async def test_notify_match_result_logs_match_received():
    """
    Test that match result receipt is logged.

    Arrange: Mock logger, create valid params
    Act: Call notify_match_result
    Assert: Logger.info called with result received message
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_result": {
            "winner_player_id": "P01",
            "drawn_number": 2,
            "status": "WIN"
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Verify logging was called multiple times
        assert mock_logger.info.call_count >= 2

        # First log should mention "result received"
        first_call = mock_logger.info.call_args_list[0]
        assert "result" in first_call[0][0].lower()


@pytest.mark.asyncio
async def test_notify_match_result_logs_match_details():
    """
    Test that match details are logged.

    Arrange: Mock logger, create params with full details
    Act: Call notify_match_result
    Assert: Logger.info called with match details
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "player_id": "P01",
        "game_result": {
            "winner_player_id": "P01",
            "drawn_number": 10,
            "choices": {
                "P01": "even",
                "P02": "odd"
            }
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Second or third log should mention "details"
        log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
        assert any("detail" in call.lower() for call in log_calls)


@pytest.mark.asyncio
async def test_notify_match_result_logs_acknowledgment():
    """
    Test that acknowledgment is logged.

    Arrange: Mock logger, create valid params
    Act: Call notify_match_result
    Assert: Logger.info called with acknowledgment message
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_result": {
            "winner_player_id": "P02",
            "drawn_number": 1
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Last log should mention acknowledgment
        last_call = mock_logger.info.call_args_list[-1]
        assert "acknowledg" in last_call[0][0].lower()


@pytest.mark.asyncio
async def test_notify_match_result_handles_missing_game_result():
    """
    Test graceful handling when game_result is missing.

    Arrange: Create params without game_result
    Act: Call notify_match_result
    Assert: Function completes without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1"
        # No game_result field
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_handles_empty_game_result():
    """
    Test handling when game_result is empty dict.

    Arrange: Create params with empty game_result
    Act: Call notify_match_result
    Assert: Function completes without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_result": {}
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_handles_missing_choices():
    """
    Test handling when choices field is missing.

    Arrange: Create game_result without choices
    Act: Call notify_match_result
    Assert: Function completes without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_result": {
            "winner_player_id": "P01",
            "drawn_number": 8
            # No choices field
        }
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_handles_empty_choices():
    """
    Test handling when choices is empty dict.

    Arrange: Create game_result with empty choices
    Act: Call notify_match_result
    Assert: Function completes without error
    """
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_result": {
            "winner_player_id": "P01",
            "drawn_number": 2,
            "choices": {}
        }
    }

    result = await notify_match_result(params)

    assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_logs_drawn_number():
    """
    Test that drawn number is logged.

    Arrange: Create params with specific drawn_number
    Act: Call notify_match_result with mocked logger
    Assert: drawn_number appears in logs
    """
    drawn_number = 7
    params = {
        "conversation_id": "convr1m1001",
        "match_id": "R1M1",
        "game_result": {
            "winner_player_id": "P02",
            "drawn_number": drawn_number
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # Check that drawn_number was logged
        log_calls = str(mock_logger.info.call_args_list)
        assert str(drawn_number) in log_calls


@pytest.mark.asyncio
async def test_notify_match_result_with_all_drawn_numbers():
    """
    Test handling all possible drawn numbers (1-10).

    Arrange: Create params for each possible drawn number
    Act: Call notify_match_result for each
    Assert: All acknowledge successfully
    """
    for number in range(1, 11):
        params = {
            "conversation_id": f"conv_{number}",
            "match_id": f"M{number}",
            "game_result": {
                "winner_player_id": "P01",
                "drawn_number": number
            }
        }

        result = await notify_match_result(params)
        assert result["acknowledged"] is True


@pytest.mark.asyncio
async def test_notify_match_result_preserves_match_id():
    """
    Test that match_id from params is used in logging.

    Arrange: Create params with specific match_id
    Act: Call notify_match_result with mocked logger
    Assert: match_id appears in logs
    """
    match_id = "CUSTOM_MATCH_XYZ"
    params = {
        "conversation_id": "convr1m1001",
        "match_id": match_id,
        "game_result": {
            "winner_player_id": "P01",
            "drawn_number": 4
        }
    }

    with patch("player_agent.handlers.result.logger") as mock_logger:
        await notify_match_result(params)

        # match_id should appear in logs
        log_calls = str(mock_logger.info.call_args_list)
        assert match_id in log_calls


@pytest.mark.asyncio
async def test_notify_match_result_multiple_calls():
    """
    Test that handler can be called multiple times successfully.

    Arrange: Create multiple different result params
    Act: Call notify_match_result multiple times
    Assert: All calls return acknowledgment
    """
    test_cases = [
        {"match_id": "M1", "drawn_number": 2, "winner_player_id": "P01"},
        {"match_id": "M2", "drawn_number": 7, "winner_player_id": "P02"},
        {"match_id": "M3", "drawn_number": 10, "winner_player_id": "P01"}
    ]

    for i, game_result in enumerate(test_cases):
        params = {
            "conversation_id": f"conv{i}",
            "match_id": game_result["match_id"],
            "game_result": game_result
        }

        result = await notify_match_result(params)
        assert result["acknowledged"] is True
