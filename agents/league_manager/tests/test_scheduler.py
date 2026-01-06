"""
Tests for round-robin scheduler and match scheduling.

Tests cover:
- Round-robin algorithm correctness
- Schedule validation
- Match ID generation
- Referee assignment and load balancing
- Edge cases (2 players, odd number of players)
"""

import pytest
from itertools import combinations
from league_manager.scheduler import (
    generate_round_robin_schedule,
    validate_schedule,
    get_schedule_stats,
    Match,
    MatchScheduler
)


class TestRoundRobinSchedule:
    """Test round-robin scheduling algorithm."""

    def test_2_players_schedule(self):
        """Test schedule with 2 players (minimum)."""
        players = ["P01", "P02"]
        schedule = generate_round_robin_schedule(players)

        # Should have 1 round with 1 match
        assert len(schedule) == 1
        assert len(schedule[0]) == 1
        assert schedule[0][0] == ("P01", "P02")

    def test_4_players_schedule(self):
        """Test schedule with 4 players (even number)."""
        players = ["P01", "P02", "P03", "P04"]
        schedule = generate_round_robin_schedule(players)

        # 4 players = 3 rounds (n-1 for even n)
        assert len(schedule) == 3

        # Total matches = 4 choose 2 = 6
        total_matches = sum(len(round_) for round_ in schedule)
        assert total_matches == 6

        # Each round should have 2 matches
        for round_matches in schedule:
            assert len(round_matches) == 2

    def test_5_players_schedule_odd(self):
        """Test schedule with 5 players (odd number, requires byes)."""
        players = ["P01", "P02", "P03", "P04", "P05"]
        schedule = generate_round_robin_schedule(players)

        # 5 players = 5 rounds (n for odd n)
        assert len(schedule) == 5

        # Total matches = 5 choose 2 = 10
        total_matches = sum(len(round_) for round_ in schedule)
        assert total_matches == 10

    def test_8_players_schedule(self):
        """Test schedule with 8 players."""
        players = [f"P{i:02d}" for i in range(1, 9)]
        schedule = generate_round_robin_schedule(players)

        # 8 players = 7 rounds
        assert len(schedule) == 7

        # Total matches = 8 choose 2 = 28
        total_matches = sum(len(round_) for round_ in schedule)
        assert total_matches == 28

    def test_all_pairs_play_exactly_once(self):
        """Verify every pair of players plays exactly once."""
        players = ["P01", "P02", "P03", "P04"]
        schedule = generate_round_robin_schedule(players)

        # Collect all matches
        all_matches = []
        for round_matches in schedule:
            all_matches.extend(round_matches)

        # Normalize matches (order doesn't matter)
        normalized_matches = set(
            tuple(sorted(match)) for match in all_matches
        )

        # Expected: all combinations of 4 players
        expected_matches = set(
            tuple(sorted(pair)) for pair in combinations(players, 2)
        )

        assert normalized_matches == expected_matches

    def test_no_player_plays_twice_in_same_round(self):
        """Verify no player plays multiple matches in same round."""
        players = ["P01", "P02", "P03", "P04", "P05", "P06"]
        schedule = generate_round_robin_schedule(players)

        for round_idx, round_matches in enumerate(schedule):
            players_in_round = []
            for match in round_matches:
                players_in_round.extend(match)

            # Check no duplicates
            assert len(players_in_round) == len(set(players_in_round)), \
                f"Player plays twice in round {round_idx + 1}"

    def test_insufficient_players_raises_error(self):
        """Test error handling for invalid input."""
        with pytest.raises(ValueError, match="at least 2 players"):
            generate_round_robin_schedule(["P01"])

        with pytest.raises(ValueError, match="at least 2 players"):
            generate_round_robin_schedule([])


class TestScheduleValidation:
    """Test schedule validation function."""

    def test_valid_schedule_passes(self):
        """Test that valid schedule passes validation."""
        players = ["P01", "P02", "P03", "P04"]
        schedule = generate_round_robin_schedule(players)
        assert validate_schedule(players, schedule) is True

    def test_duplicate_match_fails(self):
        """Test that duplicate match is detected."""
        players = ["P01", "P02", "P03"]
        schedule = [
            [("P01", "P02")],
            [("P01", "P03")],
            [("P01", "P02")]  # Duplicate
        ]
        assert validate_schedule(players, schedule) is False

    def test_player_plays_twice_in_round_fails(self):
        """Test that player playing twice in same round is detected."""
        players = ["P01", "P02", "P03"]
        schedule = [
            [("P01", "P02"), ("P01", "P03")]  # P01 plays twice
        ]
        assert validate_schedule(players, schedule) is False

    def test_missing_match_fails(self):
        """Test that missing match is detected."""
        players = ["P01", "P02", "P03"]
        schedule = [
            [("P01", "P02")],
            [("P01", "P03")]
            # Missing: ("P02", "P03")
        ]
        assert validate_schedule(players, schedule) is False


class TestScheduleStats:
    """Test schedule statistics function."""

    def test_stats_for_4_players(self):
        """Test statistics calculation."""
        players = ["P01", "P02", "P03", "P04"]
        schedule = generate_round_robin_schedule(players)
        stats = get_schedule_stats(schedule)

        assert stats["total_rounds"] == 3
        assert stats["total_matches"] == 6
        assert stats["avg_matches_per_round"] == 2.0
        assert stats["matches_per_round"] == [2, 2, 2]

    def test_stats_for_5_players(self):
        """Test statistics with odd number of players."""
        players = ["P01", "P02", "P03", "P04", "P05"]
        schedule = generate_round_robin_schedule(players)
        stats = get_schedule_stats(schedule)

        assert stats["total_rounds"] == 5
        assert stats["total_matches"] == 10
        # Some rounds will have 2 matches, some 3 (byes)
        assert sum(stats["matches_per_round"]) == 10


class TestMatchScheduler:
    """Test MatchScheduler class."""

    def test_match_id_generation(self):
        """Test match ID format."""
        scheduler = MatchScheduler("L1")
        match_id = scheduler._generate_match_id(round_number=1, match_number=5)
        assert match_id == "L1_R1_M005"

        match_id = scheduler._generate_match_id(round_number=10, match_number=123)
        assert match_id == "L1_R10_M123"

    def test_referee_assignment_load_balancing(self):
        """Test that referees are assigned evenly."""
        scheduler = MatchScheduler("L1")
        referees = [
            {"referee_id": "REF01"},
            {"referee_id": "REF02"},
            {"referee_id": "REF03"}
        ]

        # Assign 9 matches (should distribute 3-3-3)
        assigned = []
        for _ in range(9):
            ref_id = scheduler._assign_referee(referees)
            assigned.append(ref_id)

        # Check distribution
        assert assigned.count("REF01") == 3
        assert assigned.count("REF02") == 3
        assert assigned.count("REF03") == 3

    def test_create_tournament_schedule_4_players(self):
        """Test complete tournament schedule creation."""
        scheduler = MatchScheduler("L1")
        players = ["P01", "P02", "P03", "P04"]
        referees = [{"referee_id": "REF01"}]

        schedule = scheduler.create_tournament_schedule(players, referees)

        # Verify structure
        assert len(schedule) == 3  # 3 rounds
        assert sum(len(round_) for round_ in schedule) == 6  # 6 matches

        # Verify all matches are Match objects
        for round_matches in schedule:
            for match in round_matches:
                assert isinstance(match, Match)
                assert match.match_id.startswith("L1_R")
                assert match.referee_id == "REF01"

    def test_create_tournament_schedule_5_players(self):
        """Test tournament with odd number of players."""
        scheduler = MatchScheduler("L1")
        players = ["P01", "P02", "P03", "P04", "P05"]
        referees = [
            {"referee_id": "REF01"},
            {"referee_id": "REF02"}
        ]

        schedule = scheduler.create_tournament_schedule(players, referees)

        # Verify structure
        assert len(schedule) == 5  # 5 rounds
        assert sum(len(round_) for round_ in schedule) == 10  # 10 matches

    def test_referee_workload_tracking(self):
        """Test that referee workload is tracked correctly."""
        scheduler = MatchScheduler("L1")
        players = ["P01", "P02", "P03", "P04"]
        referees = [
            {"referee_id": "REF01"},
            {"referee_id": "REF02"}
        ]

        scheduler.create_tournament_schedule(players, referees)

        # 6 matches distributed across 2 referees = 3 each
        assert scheduler.referee_workload["REF01"] == 3
        assert scheduler.referee_workload["REF02"] == 3

    def test_insufficient_players_raises_error(self):
        """Test error handling for insufficient players."""
        scheduler = MatchScheduler("L1")
        referees = [{"referee_id": "REF01"}]

        with pytest.raises(ValueError, match="at least 2 players"):
            scheduler.create_tournament_schedule(["P01"], referees)

    def test_no_referees_raises_error(self):
        """Test error handling for no referees."""
        scheduler = MatchScheduler("L1")
        players = ["P01", "P02"]

        with pytest.raises(ValueError, match="at least 1 referee"):
            scheduler.create_tournament_schedule(players, [])

    def test_match_to_dict(self):
        """Test Match.to_dict() method."""
        match = Match(
            match_id="L1_R1_M001",
            player_a_id="P01",
            player_b_id="P02",
            referee_id="REF01",
            round_number=1
        )

        match_dict = match.to_dict()

        assert match_dict == {
            "match_id": "L1_R1_M001",
            "player_a_id": "P01",
            "player_b_id": "P02",
            "referee_id": "REF01",
            "round_number": 1
        }


class TestIntegration:
    """Integration tests for complete workflow."""

    def test_full_tournament_2_players(self):
        """Test complete tournament with 2 players."""
        scheduler = MatchScheduler("L1")
        players = ["P01", "P02"]
        referees = [{"referee_id": "REF01"}]

        schedule = scheduler.create_tournament_schedule(players, referees)

        # 1 round, 1 match
        assert len(schedule) == 1
        assert len(schedule[0]) == 1

        match = schedule[0][0]
        assert match.player_a_id == "P01"
        assert match.player_b_id == "P02"
        assert match.match_id == "L1_R1_M001"

    def test_full_tournament_8_players_2_referees(self):
        """Test complete tournament with 8 players and 2 referees."""
        scheduler = MatchScheduler("L1")
        players = [f"P{i:02d}" for i in range(1, 9)]
        referees = [
            {"referee_id": "REF01"},
            {"referee_id": "REF02"}
        ]

        schedule = scheduler.create_tournament_schedule(players, referees)

        # Verify all players play all other players
        all_pairings = set()
        for round_matches in schedule:
            for match in round_matches:
                pairing = tuple(sorted([match.player_a_id, match.player_b_id]))
                all_pairings.add(pairing)

        expected_pairings = set(
            tuple(sorted(pair)) for pair in combinations(players, 2)
        )

        assert all_pairings == expected_pairings

        # Verify referee load balancing (28 matches / 2 referees = 14 each)
        assert scheduler.referee_workload["REF01"] == 14
        assert scheduler.referee_workload["REF02"] == 14

    def test_schedule_validation_after_creation(self):
        """Test that created schedules pass validation."""
        scheduler = MatchScheduler("L1")
        players = ["P01", "P02", "P03", "P04", "P05", "P06"]
        referees = [{"referee_id": "REF01"}]

        schedule = scheduler.create_tournament_schedule(players, referees)

        # Convert Match objects to tuples for validation
        tuple_schedule = [
            [(m.player_a_id, m.player_b_id) for m in round_matches]
            for round_matches in schedule
        ]

        assert validate_schedule(players, tuple_schedule) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
