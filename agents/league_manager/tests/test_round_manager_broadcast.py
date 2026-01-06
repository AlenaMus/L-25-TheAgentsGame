"""
Integration tests for RoundManager with Broadcaster.

Tests the complete round lifecycle with message broadcasting.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from league_manager.handlers.round_manager import RoundManager
from league_manager.broadcast import Broadcaster, MessageBuilder
from league_manager.standings import StandingsCalculator
from league_manager.scheduler import Match


@pytest.fixture
def mock_agent_store():
    """Mock agent store with sample players."""
    store = MagicMock()
    store.get_all_players.return_value = [
        {"player_id": "P01", "endpoint": "http://localhost:9001/mcp"},
        {"player_id": "P02", "endpoint": "http://localhost:9002/mcp"}
    ]
    return store


@pytest.fixture
def broadcaster():
    """Create broadcaster instance."""
    return Broadcaster(timeout=5.0, max_retries=2)


@pytest.fixture
def message_builder():
    """Create message builder instance."""
    return MessageBuilder(league_id="test_league")


@pytest.fixture
def standings_calculator():
    """Create standings calculator."""
    calc = StandingsCalculator()
    calc.add_player("P01", "Alice")
    calc.add_player("P02", "Bob")
    return calc


@pytest.fixture
def round_manager(standings_calculator, broadcaster, message_builder, mock_agent_store):
    """Create round manager with all dependencies."""
    return RoundManager(
        standings_calculator=standings_calculator,
        broadcaster=broadcaster,
        message_builder=message_builder,
        agent_store=mock_agent_store,
        league_id="test_league"
    )


@pytest.fixture
def sample_schedule():
    """Create sample tournament schedule."""
    return [
        [
            Match(
                match_id="R1M1",
                round_number=1,
                player_a_id="P01",
                player_b_id="P02",
                referee_id="REF01"
            )
        ]
    ]


class TestRoundManagerBroadcast:
    """Test RoundManager with broadcast integration."""

    @pytest.mark.asyncio
    async def test_start_round_broadcasts_announcement(
        self, round_manager, sample_schedule, mock_agent_store
    ):
        """Test that starting a round broadcasts announcement."""
        round_manager.initialize_tournament(sample_schedule)

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            announcement = await round_manager.start_round(1)

            assert announcement["message_type"] == "ROUND_ANNOUNCEMENT"
            assert announcement["round_id"] == 1
            assert len(announcement["matches"]) == 1
            assert mock_agent_store.get_all_players.called

    @pytest.mark.asyncio
    async def test_complete_round_broadcasts_completion(
        self, round_manager, sample_schedule, mock_agent_store
    ):
        """Test that completing a round broadcasts completion message."""
        round_manager.initialize_tournament(sample_schedule)

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Start round first
            await round_manager.start_round(1)

            # Complete round
            completion = await round_manager.complete_round(1)

            assert completion["message_type"] == "ROUND_COMPLETED"
            assert completion["round_id"] == 1
            assert completion["matches_completed"] == 1
            assert completion["next_round_id"] is None  # Only one round
            assert mock_agent_store.get_all_players.called

    @pytest.mark.asyncio
    async def test_tournament_end_broadcast(
        self, round_manager, sample_schedule, standings_calculator, mock_agent_store
    ):
        """Test tournament end broadcast."""
        round_manager.initialize_tournament(sample_schedule)

        # Add some standings data
        standings_calculator.record_match_result("R1M1", "P01", "P02", "P01")

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            message = await round_manager.broadcast_tournament_end()

            assert message["message_type"] == "TOURNAMENT_END"
            assert message["total_rounds"] == 1
            assert message["total_matches"] == 1
            assert message["champion"] is not None
            assert message["champion"]["player_id"] == "P01"
            assert len(message["final_standings"]) == 2

    @pytest.mark.asyncio
    async def test_broadcast_handles_failed_deliveries(
        self, round_manager, sample_schedule
    ):
        """Test that failed deliveries don't crash round manager."""
        round_manager.initialize_tournament(sample_schedule)

        async def mock_post(*args, **kwargs):
            # Simulate failure
            import httpx
            raise httpx.TimeoutException("Timeout")

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post

            # Should not raise exception
            announcement = await round_manager.start_round(1)

            # Announcement still created
            assert announcement["message_type"] == "ROUND_ANNOUNCEMENT"

    @pytest.mark.asyncio
    async def test_round_lifecycle_with_broadcasts(
        self, round_manager, sample_schedule, mock_agent_store
    ):
        """Test complete round lifecycle with all broadcasts."""
        round_manager.initialize_tournament(sample_schedule)

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # 1. Start round (broadcasts ROUND_ANNOUNCEMENT)
            announcement = await round_manager.start_round(1)
            assert announcement["message_type"] == "ROUND_ANNOUNCEMENT"

            # 2. Mark match complete
            round_manager.mark_match_complete("R1M1", 1)

            # 3. Complete round (broadcasts ROUND_COMPLETED)
            completion = await round_manager.complete_round(1)
            assert completion["message_type"] == "ROUND_COMPLETED"

            # 4. Tournament end (broadcasts TOURNAMENT_END)
            assert round_manager.is_tournament_complete()
            end = await round_manager.broadcast_tournament_end()
            assert end["message_type"] == "TOURNAMENT_END"

            # Verify get_all_players was called for each broadcast
            assert mock_agent_store.get_all_players.call_count >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
