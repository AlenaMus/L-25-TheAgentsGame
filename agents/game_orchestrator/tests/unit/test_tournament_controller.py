"""
Unit tests for TournamentController.

Tests tournament flow management and state transitions.
"""

import pytest
from unittest.mock import AsyncMock, patch
from orchestrator.tournament.controller import (
    TournamentController,
    TournamentState
)


@pytest.fixture
def tournament_controller():
    """Create tournament controller instance."""
    return TournamentController("http://localhost:8000/mcp")


@pytest.mark.asyncio
async def test_start_tournament_success(tournament_controller):
    """Test successful tournament start."""
    mock_schedule = {
        "rounds": [
            {"round_id": 1, "matches": []},
            {"round_id": 2, "matches": []},
            {"round_id": 3, "matches": []}
        ]
    }

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": mock_schedule}
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        success = await tournament_controller.start_tournament()

        assert success is True
        assert tournament_controller.total_rounds == 3
        assert tournament_controller.state == TournamentState.SCHEDULED


@pytest.mark.asyncio
async def test_start_tournament_no_schedule(tournament_controller):
    """Test tournament start fails when no schedule."""
    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": {}}
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        success = await tournament_controller.start_tournament()

        assert success is False


@pytest.mark.asyncio
async def test_start_next_round(tournament_controller):
    """Test starting next round."""
    tournament_controller.total_rounds = 3
    tournament_controller.state = TournamentState.SCHEDULED

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        success = await tournament_controller.start_next_round()

        assert success is True
        assert tournament_controller.current_round == 1
        assert tournament_controller.state == TournamentState.ROUND_ANNOUNCED


@pytest.mark.asyncio
async def test_start_next_round_all_complete(tournament_controller):
    """Test starting round when all rounds complete."""
    tournament_controller.total_rounds = 3
    tournament_controller.current_round = 3

    success = await tournament_controller.start_next_round()

    assert success is False
    assert tournament_controller.state == TournamentState.TOURNAMENT_COMPLETED


@pytest.mark.asyncio
async def test_pause_tournament(tournament_controller):
    """Test pausing tournament."""
    tournament_controller.state = TournamentState.ROUND_IN_PROGRESS

    success = await tournament_controller.pause_tournament()

    assert success is True
    assert tournament_controller.state == TournamentState.PAUSED


@pytest.mark.asyncio
async def test_resume_tournament(tournament_controller):
    """Test resuming paused tournament."""
    tournament_controller.state = TournamentState.PAUSED

    success = await tournament_controller.resume_tournament()

    assert success is True
    assert tournament_controller.state == TournamentState.ROUND_IN_PROGRESS


@pytest.mark.asyncio
async def test_resume_not_paused(tournament_controller):
    """Test resuming tournament that isn't paused."""
    tournament_controller.state = TournamentState.ROUND_IN_PROGRESS

    success = await tournament_controller.resume_tournament()

    assert success is False


@pytest.mark.asyncio
async def test_monitor_round_progress(tournament_controller):
    """Test monitoring round progress."""
    tournament_controller.current_round = 1
    tournament_controller.total_rounds = 3
    tournament_controller.state = TournamentState.ROUND_IN_PROGRESS

    mock_standings = [
        {"player_id": "P01", "points": 3},
        {"player_id": "P02", "points": 0}
    ]

    with patch("httpx.AsyncClient") as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {"standings": mock_standings}
        }
        mock_client.return_value.__aenter__.return_value.post = AsyncMock(
            return_value=mock_response
        )

        progress = await tournament_controller.monitor_round_progress()

        assert progress["round"] == 1
        assert progress["total_rounds"] == 3
        assert progress["state"] == TournamentState.ROUND_IN_PROGRESS.value
        assert len(progress["standings"]) == 2


@pytest.mark.asyncio
async def test_start_round_while_paused(tournament_controller):
    """Test cannot start round while paused."""
    tournament_controller.state = TournamentState.PAUSED
    tournament_controller.total_rounds = 3

    success = await tournament_controller.start_next_round()

    assert success is False
