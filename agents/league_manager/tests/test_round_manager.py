"""
Tests for round management and match result reporting.

Tests cover:
- Round creation and initialization
- Round announcement message format
- Match completion tracking
- Round completion detection
- Multi-round tournament flow
- Match result reporting
- Standings updates after results
"""

import pytest
from league_manager.handlers import (
    RoundManager,
    RoundStatus,
    handle_match_result_report
)
from league_manager.standings import StandingsCalculator
from league_manager.scheduler import Match, MatchScheduler


class TestRoundManager:
    """Test round management functionality."""

    @pytest.fixture
    def standings_calculator(self):
        """Create standings calculator with players."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")
        calc.add_player("P03", "Charlie")
        calc.add_player("P04", "Diana")
        return calc

    @pytest.fixture
    def tournament_schedule(self):
        """Create sample tournament schedule (4 players, 3 rounds)."""
        scheduler = MatchScheduler()
        player_ids = ["P01", "P02", "P03", "P04"]
        referees = [{"referee_id": "REF01"}]
        return scheduler.create_tournament_schedule(player_ids, referees)

    @pytest.fixture
    def round_manager(self, standings_calculator, tournament_schedule):
        """Create initialized round manager."""
        manager = RoundManager(standings_calculator)
        manager.initialize_tournament(tournament_schedule)
        return manager

    def test_initialize_tournament(self, standings_calculator):
        """Test tournament initialization."""
        manager = RoundManager(standings_calculator)

        # Create simple 2-round schedule
        schedule = [
            [Match("R1M1", "P01", "P02", "REF01", 1)],
            [Match("R2M1", "P03", "P04", "REF01", 2)]
        ]

        manager.initialize_tournament(schedule)

        assert manager.total_rounds == 2
        assert manager.current_round is None
        assert len(manager.round_matches) == 2
        assert manager.round_status[1] == RoundStatus.PENDING
        assert manager.round_status[2] == RoundStatus.PENDING

    def test_start_round_creates_announcement(self, round_manager):
        """Test starting a round creates correct announcement message."""
        announcement = round_manager.start_round(1)

        assert announcement["message_type"] == "ROUND_ANNOUNCEMENT"
        assert announcement["protocol"] == "league.v2"
        assert announcement["round_id"] == 1
        assert announcement["league_id"] == "league_2025_even_odd"
        assert "matches" in announcement
        assert len(announcement["matches"]) > 0

        # Check match format
        match = announcement["matches"][0]
        assert "match_id" in match
        assert "player_A_id" in match
        assert "player_B_id" in match
        assert "game_type" in match
        assert match["game_type"] == "even_odd"

    def test_start_round_updates_state(self, round_manager):
        """Test starting round updates state correctly."""
        round_manager.start_round(1)

        assert round_manager.current_round == 1
        assert round_manager.round_status[1] == RoundStatus.IN_PROGRESS

    def test_cannot_start_round_twice(self, round_manager):
        """Test cannot start same round twice."""
        round_manager.start_round(1)

        with pytest.raises(ValueError, match="already IN_PROGRESS"):
            round_manager.start_round(1)

    def test_mark_match_complete(self, round_manager):
        """Test marking individual match as complete."""
        round_manager.start_round(1)

        matches = round_manager.round_matches[1]
        first_match_id = matches[0].match_id

        # Complete first match (round not done if there are multiple)
        round_complete = round_manager.mark_match_complete(
            first_match_id, 1
        )

        if len(matches) > 1:
            assert not round_complete
        else:
            assert round_complete

    def test_round_completion_detection(self, round_manager):
        """Test round completes when all matches finish."""
        round_manager.start_round(1)

        matches = round_manager.round_matches[1]

        # Complete all matches except last
        for match in matches[:-1]:
            is_complete = round_manager.mark_match_complete(
                match.match_id, 1
            )
            assert not is_complete

        # Complete last match
        is_complete = round_manager.mark_match_complete(
            matches[-1].match_id, 1
        )
        assert is_complete

    def test_complete_round_message(self, round_manager):
        """Test round completion message format."""
        round_manager.start_round(1)

        # Complete all matches
        for match in round_manager.round_matches[1]:
            round_manager.mark_match_complete(match.match_id, 1)

        completion_msg = round_manager.complete_round(1)

        assert completion_msg["message_type"] == "ROUND_COMPLETED"
        assert completion_msg["protocol"] == "league.v2"
        assert completion_msg["round_id"] == 1
        assert completion_msg["matches_completed"] > 0
        assert "next_round_id" in completion_msg

    def test_next_round_id_in_completion(self, round_manager):
        """Test next_round_id is correct in completion message."""
        round_manager.start_round(1)

        for match in round_manager.round_matches[1]:
            round_manager.mark_match_complete(match.match_id, 1)

        completion_msg = round_manager.complete_round(1)

        # Should have next round (tournament has 3 rounds)
        assert completion_msg["next_round_id"] == 2

    def test_final_round_completion(self, round_manager):
        """Test final round completion has no next round."""
        # Start and complete all rounds
        for round_num in range(1, round_manager.total_rounds + 1):
            round_manager.start_round(round_num)
            for match in round_manager.round_matches[round_num]:
                round_manager.mark_match_complete(match.match_id, round_num)

            if round_num == round_manager.total_rounds:
                completion_msg = round_manager.complete_round(round_num)
                assert completion_msg["next_round_id"] is None

    def test_tournament_completion_check(self, round_manager):
        """Test tournament completion detection."""
        assert not round_manager.is_tournament_complete()

        # Complete all rounds
        for round_num in range(1, round_manager.total_rounds + 1):
            round_manager.start_round(round_num)
            for match in round_manager.round_matches[round_num]:
                round_manager.mark_match_complete(match.match_id, round_num)
            round_manager.complete_round(round_num)

        assert round_manager.is_tournament_complete()


class TestMatchResultReporting:
    """Test match result reporting handler."""

    @pytest.fixture
    def standings_calculator(self):
        """Create standings calculator with players."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")
        return calc

    @pytest.fixture
    def round_manager(self, standings_calculator):
        """Create round manager with simple schedule."""
        manager = RoundManager(standings_calculator)
        schedule = [
            [Match("R1M1", "P01", "P02", "REF01", 1)]
        ]
        manager.initialize_tournament(schedule)
        manager.start_round(1)
        return manager

    @pytest.mark.asyncio
    async def test_handle_match_result_win(
        self, standings_calculator, round_manager
    ):
        """Test handling match result with winner."""
        result_params = {
            "protocol": "league.v2",
            "message_type": "MATCH_RESULT_REPORT",
            "match_id": "R1M1",
            "round_id": 1,
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0}
            }
        }

        response = await handle_match_result_report(
            result_params,
            standings_calculator,
            round_manager,
            "league_2025_even_odd"
        )

        assert response["acknowledged"] is True
        assert response["match_id"] == "R1M1"

        # Check standings updated
        standings = standings_calculator.get_standings()
        winner = next(p for p in standings if p.player_id == "P01")
        assert winner.points == 3
        assert winner.wins == 1

    @pytest.mark.asyncio
    async def test_handle_match_result_tie(
        self, standings_calculator, round_manager
    ):
        """Test handling match result with tie."""
        result_params = {
            "match_id": "R1M1",
            "round_id": 1,
            "result": {
                "winner": None,
                "score": {"P01": 1, "P02": 1}
            }
        }

        response = await handle_match_result_report(
            result_params,
            standings_calculator,
            round_manager,
            "league_2025_even_odd"
        )

        assert response["acknowledged"] is True

        # Check standings
        standings = standings_calculator.get_standings()
        for player in standings:
            assert player.points == 1
            assert player.ties == 1

    @pytest.mark.asyncio
    async def test_round_completion_signaled(
        self, standings_calculator, round_manager
    ):
        """Test round completion is signaled in response."""
        result_params = {
            "match_id": "R1M1",
            "round_id": 1,
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0}
            }
        }

        response = await handle_match_result_report(
            result_params,
            standings_calculator,
            round_manager,
            "league_2025_even_odd"
        )

        # Should signal round complete (only 1 match in round)
        assert response["round_complete"] is True

    @pytest.mark.asyncio
    async def test_invalid_match_result(
        self, standings_calculator, round_manager
    ):
        """Test handling invalid match result."""
        result_params = {
            "match_id": None,  # Invalid
            "round_id": 1
        }

        response = await handle_match_result_report(
            result_params,
            standings_calculator,
            round_manager,
            "league_2025_even_odd"
        )

        assert response["acknowledged"] is False
        assert "error" in response


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
