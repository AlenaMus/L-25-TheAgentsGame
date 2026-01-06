"""
Tests for broadcast system.

Tests broadcasting messages to players and referees with concurrent
delivery, timeout handling, and retry logic.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
from league_manager.broadcast import Broadcaster, MessageBuilder


@pytest.fixture
def broadcaster():
    """Create broadcaster instance."""
    return Broadcaster(timeout=5.0, max_retries=2)


@pytest.fixture
def message_builder():
    """Create message builder instance."""
    return MessageBuilder(league_id="test_league")


@pytest.fixture
def sample_players():
    """Sample player list."""
    return [
        {"player_id": "P01", "endpoint": "http://localhost:9001/mcp"},
        {"player_id": "P02", "endpoint": "http://localhost:9002/mcp"},
        {"player_id": "P03", "endpoint": "http://localhost:9003/mcp"}
    ]


@pytest.fixture
def sample_referees():
    """Sample referee list."""
    return [
        {"referee_id": "REF01", "endpoint": "http://localhost:8001/mcp"},
        {"referee_id": "REF02", "endpoint": "http://localhost:8002/mcp"}
    ]


class TestBroadcaster:
    """Test Broadcaster class."""

    @pytest.mark.asyncio
    async def test_broadcast_to_players_success(self, broadcaster, sample_players):
        """Test successful broadcast to all players."""
        message = {"message_type": "ROUND_ANNOUNCEMENT", "round_id": 1}

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            report = await broadcaster.broadcast_to_players(sample_players, message)

            assert report.total == 3
            assert report.successful == 3
            assert report.failed == 0
            assert len(report.failed_agents) == 0

    @pytest.mark.asyncio
    async def test_broadcast_with_timeout(self, broadcaster, sample_players):
        """Test broadcast with timeout on one agent."""
        message = {"message_type": "ROUND_ANNOUNCEMENT"}

        async def mock_post(*args, **kwargs):
            # Simulate timeout on second player
            if "9002" in str(args):
                raise httpx.TimeoutException("Timeout")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post

            report = await broadcaster.broadcast_to_players(sample_players, message)

            assert report.total == 3
            assert report.successful == 2
            assert report.failed == 1
            assert "P02" in report.failed_agents

    @pytest.mark.asyncio
    async def test_broadcast_with_retry_success(self, broadcaster):
        """Test retry mechanism succeeds on second attempt."""
        players = [{"player_id": "P01", "endpoint": "http://localhost:9001/mcp"}]
        message = {"message_type": "TEST"}

        attempt_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise httpx.TimeoutException("First attempt timeout")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            return mock_response

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post

            report = await broadcaster.broadcast_to_players(players, message)

            assert report.successful == 1
            assert attempt_count == 2

    @pytest.mark.asyncio
    async def test_broadcast_http_error(self, broadcaster, sample_players):
        """Test broadcast with HTTP error."""
        message = {"message_type": "TEST"}

        async def mock_post(*args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status = MagicMock(
                side_effect=httpx.HTTPStatusError("Error", request=MagicMock(), response=mock_response)
            )
            return mock_response

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post = mock_post

            report = await broadcaster.broadcast_to_players(sample_players, message)

            assert report.failed == 3
            assert report.successful == 0

    @pytest.mark.asyncio
    async def test_broadcast_to_referees(self, broadcaster, sample_referees):
        """Test broadcast to referees."""
        message = {"message_type": "MATCH_ASSIGNMENT"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            report = await broadcaster.broadcast_to_referees(sample_referees, message)

            assert report.total == 2
            assert report.successful == 2

    @pytest.mark.asyncio
    async def test_broadcast_to_all(self, broadcaster, sample_players, sample_referees):
        """Test broadcast to both players and referees."""
        message = {"message_type": "TOURNAMENT_START"}

        with patch('httpx.AsyncClient') as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            report = await broadcaster.broadcast_to_all(
                sample_players, sample_referees, message
            )

            assert report.total == 5
            assert report.successful == 5

    @pytest.mark.asyncio
    async def test_broadcast_empty_list(self, broadcaster):
        """Test broadcast with empty agent list."""
        message = {"message_type": "TEST"}
        report = await broadcaster.broadcast_to_players([], message)

        assert report.total == 0
        assert report.successful == 0

    @pytest.mark.asyncio
    async def test_agent_missing_endpoint(self, broadcaster):
        """Test agent with missing endpoint."""
        players = [{"player_id": "P01"}]  # No endpoint
        message = {"message_type": "TEST"}

        report = await broadcaster.broadcast_to_players(players, message)

        assert report.failed == 1
        assert "P01" in report.failed_agents


class TestMessageBuilder:
    """Test MessageBuilder class."""

    def test_build_round_announcement(self, message_builder):
        """Test building round announcement message."""
        matches = [
            {
                "match_id": "R1M1",
                "player_A_id": "P01",
                "player_B_id": "P02"
            }
        ]

        msg = message_builder.build_round_announcement(round_id=1, matches=matches)

        assert msg["protocol"] == "league.v2"
        assert msg["message_type"] == "ROUND_ANNOUNCEMENT"
        assert msg["sender"] == "league:league_manager"
        assert msg["league_id"] == "test_league"
        assert msg["round_id"] == 1
        assert msg["matches"] == matches
        assert "timestamp" in msg
        assert "conversation_id" in msg

    def test_build_round_completed(self, message_builder):
        """Test building round completed message."""
        msg = message_builder.build_round_completed(
            round_id=1,
            matches_completed=2,
            next_round_id=2
        )

        assert msg["message_type"] == "ROUND_COMPLETED"
        assert msg["round_id"] == 1
        assert msg["matches_completed"] == 2
        assert msg["next_round_id"] == 2

    def test_build_round_completed_final_round(self, message_builder):
        """Test round completed with no next round."""
        msg = message_builder.build_round_completed(
            round_id=3,
            matches_completed=2,
            next_round_id=None
        )

        assert msg["next_round_id"] is None

    def test_build_tournament_start(self, message_builder):
        """Test building tournament start message."""
        msg = message_builder.build_tournament_start(
            total_rounds=3,
            total_matches=6,
            player_count=4
        )

        assert msg["message_type"] == "TOURNAMENT_START"
        assert msg["total_rounds"] == 3
        assert msg["total_matches"] == 6
        assert msg["player_count"] == 4

    def test_build_tournament_end(self, message_builder):
        """Test building tournament end message."""
        champion = {"player_id": "P01", "points": 9}
        standings = [
            {"rank": 1, "player_id": "P01", "points": 9},
            {"rank": 2, "player_id": "P02", "points": 6}
        ]

        msg = message_builder.build_tournament_end(
            total_rounds=3,
            total_matches=6,
            champion=champion,
            final_standings=standings
        )

        assert msg["message_type"] == "TOURNAMENT_END"
        assert msg["champion"] == champion
        assert msg["final_standings"] == standings

    def test_build_standings_update(self, message_builder):
        """Test building standings update message."""
        standings = [
            {"rank": 1, "player_id": "P01", "points": 3}
        ]

        msg = message_builder.build_standings_update(round_id=1, standings=standings)

        assert msg["message_type"] == "LEAGUE_STANDINGS_UPDATE"
        assert msg["round_id"] == 1
        assert msg["standings"] == standings

    def test_timestamp_format(self, message_builder):
        """Test timestamp format is correct."""
        msg = message_builder.build_tournament_start(
            total_rounds=1, total_matches=1, player_count=2
        )

        timestamp = msg["timestamp"]
        # Format: 20250121T120000Z
        assert len(timestamp) == 16
        assert timestamp[8] == 'T'
        assert timestamp[-1] == 'Z'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
