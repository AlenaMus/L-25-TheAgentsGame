"""
Comprehensive tests for standings calculation and match tracking.

Tests cover:
- Simple scenarios (2 players, 1 match)
- Tie scenarios (all tied)
- Tiebreaker rules (head-to-head)
- Full tournament (8 players, complete round-robin)
- Points calculation
- Ranking accuracy
"""

import pytest
from league_manager.standings import (
    StandingsCalculator,
    PlayerStanding,
    MatchTracker,
    MatchResult
)


class TestMatchTracker:
    """Test match tracking functionality."""

    def test_record_single_match(self):
        """Test recording a single match result."""
        tracker = MatchTracker()
        tracker.record_match("R1M1", "P01", "P02", "P01", "WIN")

        assert len(tracker.matches) == 1
        assert tracker.get_head_to_head("P01", "P02") == "W"
        assert tracker.get_head_to_head("P02", "P01") == "L"

    def test_record_tie(self):
        """Test recording a tie result."""
        tracker = MatchTracker()
        tracker.record_match("R1M1", "P01", "P02", None, "TIE")

        assert tracker.get_head_to_head("P01", "P02") == "T"
        assert tracker.get_head_to_head("P02", "P01") == "T"

    def test_player_statistics(self):
        """Test player statistics tracking."""
        tracker = MatchTracker()
        tracker.record_match("R1M1", "P01", "P02", "P01", "WIN")
        tracker.record_match("R1M2", "P01", "P03", None, "TIE")

        p01_stats = tracker.get_player_stats("P01")
        assert p01_stats["wins"] == 1
        assert p01_stats["losses"] == 0
        assert p01_stats["ties"] == 1
        assert p01_stats["matches_played"] == 2

        p02_stats = tracker.get_player_stats("P02")
        assert p02_stats["wins"] == 0
        assert p02_stats["losses"] == 1
        assert p02_stats["ties"] == 0
        assert p02_stats["matches_played"] == 1

    def test_invalid_winner(self):
        """Test that invalid winner raises error."""
        tracker = MatchTracker()
        with pytest.raises(ValueError, match="Winner .* not in match players"):
            tracker.record_match("R1M1", "P01", "P02", "P03", "WIN")


class TestStandingsCalculator:
    """Test standings calculation with tiebreakers."""

    def test_add_player(self):
        """Test adding players to standings."""
        calc = StandingsCalculator()
        standing = calc.add_player("P01", "Alice")

        assert standing.player_id == "P01"
        assert standing.display_name == "Alice"
        assert standing.wins == 0
        assert standing.points == 0

    def test_simple_scenario_one_match(self):
        """Test simple scenario: 2 players, 1 match."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")

        calc.record_match_result("R1M1", "P01", "P02", "P01")

        standings = calc.get_standings()
        assert len(standings) == 2

        # P01 should be rank 1 with 3 points
        assert standings[0].player_id == "P01"
        assert standings[0].rank == 1
        assert standings[0].wins == 1
        assert standings[0].losses == 0
        assert standings[0].points == 3

        # P02 should be rank 2 with 0 points
        assert standings[1].player_id == "P02"
        assert standings[1].rank == 2
        assert standings[1].wins == 0
        assert standings[1].losses == 1
        assert standings[1].points == 0

    def test_tie_scenario(self):
        """Test tie scenario: 3 players, all tied on points."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")
        calc.add_player("P03", "Charlie")

        # All ties
        calc.record_match_result("R1M1", "P01", "P02", None)
        calc.record_match_result("R1M2", "P01", "P03", None)
        calc.record_match_result("R1M3", "P02", "P03", None)

        standings = calc.get_standings()

        # All should have 2 points (1 point per tie, 2 matches each)
        for player in standings:
            assert player.points == 2
            assert player.ties == 2

        # Should be sorted alphabetically: P01, P02, P03
        assert standings[0].player_id == "P01"
        assert standings[1].player_id == "P02"
        assert standings[2].player_id == "P03"

    def test_head_to_head_tiebreaker(self):
        """Test tiebreaker: head-to-head when 2 players tied on points."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")
        calc.add_player("P03", "Charlie")
        calc.add_player("P04", "David")

        # P01 beats P02, both win against others
        calc.record_match_result("R1M1", "P01", "P02", "P01")
        calc.record_match_result("R1M2", "P01", "P03", "P03")
        calc.record_match_result("R1M3", "P02", "P04", "P02")

        standings = calc.get_standings()

        # P01 and P02 both have 3 points, but P01 won head-to-head
        p01_standing = next(s for s in standings if s.player_id == "P01")
        p02_standing = next(s for s in standings if s.player_id == "P02")
        p03_standing = next(s for s in standings if s.player_id == "P03")

        assert p01_standing.points == 3
        assert p02_standing.points == 3
        assert p03_standing.points == 3

        # P01 should rank higher than P02 due to head-to-head
        assert p01_standing.rank < p02_standing.rank

    def test_points_calculation(self):
        """Test that points are calculated correctly (W=3, T=1, L=0)."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")
        calc.add_player("P03", "Charlie")

        # P01: 1 win, 1 tie = 4 points
        calc.record_match_result("R1M1", "P01", "P02", "P01")
        calc.record_match_result("R1M2", "P01", "P03", None)

        p01 = calc.get_player_standing("P01")
        assert p01.wins == 1
        assert p01.ties == 1
        assert p01.losses == 0
        assert p01.points == 4  # 3 + 1

    def test_full_tournament_4_players(self):
        """Test complete round-robin: 4 players, 6 matches."""
        calc = StandingsCalculator()
        players = ["P01", "P02", "P03", "P04"]
        for pid in players:
            calc.add_player(pid, f"Player {pid}")

        # Round 1
        calc.record_match_result("R1M1", "P01", "P02", "P01")
        calc.record_match_result("R1M2", "P03", "P04", "P03")

        # Round 2
        calc.record_match_result("R2M1", "P01", "P03", "P03")
        calc.record_match_result("R2M2", "P02", "P04", "P02")

        # Round 3
        calc.record_match_result("R3M1", "P01", "P04", None)
        calc.record_match_result("R3M2", "P02", "P03", "P03")

        standings = calc.get_standings()

        # Verify all players played 3 matches
        for player in standings:
            assert player.matches_played == 3

        # P03 should be top (3 wins = 9 points)
        p03 = next(s for s in standings if s.player_id == "P03")
        assert p03.wins == 3
        assert p03.losses == 0
        assert p03.points == 9
        assert p03.rank == 1

    def test_full_tournament_8_players(self):
        """Test large tournament: 8 players, complete round-robin."""
        calc = StandingsCalculator()
        players = [f"P{i:02d}" for i in range(1, 9)]

        for pid in players:
            calc.add_player(pid, f"Player {pid}")

        # Simulate 28 matches (8 * 7 / 2)
        match_results = [
            ("P01", "P02", "P01"), ("P01", "P03", "P01"), ("P01", "P04", "P04"),
            ("P01", "P05", "P01"), ("P01", "P06", None), ("P01", "P07", "P01"),
            ("P01", "P08", "P01"),
            ("P02", "P03", "P02"), ("P02", "P04", "P02"), ("P02", "P05", "P05"),
            ("P02", "P06", "P02"), ("P02", "P07", None), ("P02", "P08", "P02"),
            ("P03", "P04", "P03"), ("P03", "P05", "P03"), ("P03", "P06", "P03"),
            ("P03", "P07", "P03"), ("P03", "P08", None),
            ("P04", "P05", "P04"), ("P04", "P06", "P04"), ("P04", "P07", "P04"),
            ("P04", "P08", "P04"),
            ("P05", "P06", "P05"), ("P05", "P07", "P05"), ("P05", "P08", "P05"),
            ("P06", "P07", "P06"), ("P06", "P08", "P06"),
            ("P07", "P08", "P07")
        ]

        for i, (pa, pb, winner) in enumerate(match_results):
            calc.record_match_result(f"R{i+1}M1", pa, pb, winner)

        standings = calc.get_standings()

        # Verify all players played 7 matches
        for player in standings:
            assert player.matches_played == 7

        # Rankings should be properly assigned
        ranks = [s.rank for s in standings]
        assert ranks == list(range(1, 9))

        # Verify standings are sorted by points
        for i in range(len(standings) - 1):
            assert standings[i].points >= standings[i + 1].points

    def test_alphabetical_tiebreaker(self):
        """Test that alphabetical order is used when all else equal."""
        calc = StandingsCalculator()
        calc.add_player("P03", "Charlie")
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")

        # No matches - all have 0 points

        standings = calc.get_standings()

        # Should be alphabetical by player_id
        assert standings[0].player_id == "P01"
        assert standings[1].player_id == "P02"
        assert standings[2].player_id == "P03"

    def test_record_match_unknown_player(self):
        """Test that recording match with unknown player raises error."""
        calc = StandingsCalculator()
        calc.add_player("P01", "Alice")

        with pytest.raises(KeyError, match="Player P02 not in standings"):
            calc.record_match_result("R1M1", "P01", "P02", "P01")


class TestIntegration:
    """Integration tests for full standings workflow."""

    def test_complete_workflow(self):
        """Test complete workflow: add players, record matches, get standings."""
        tracker = MatchTracker()
        calc = StandingsCalculator(tracker)

        # Register 4 players
        calc.add_player("P01", "Alice")
        calc.add_player("P02", "Bob")
        calc.add_player("P03", "Charlie")
        calc.add_player("P04", "David")

        # Play round-robin tournament
        calc.record_match_result("R1M1", "P01", "P02", "P01")
        calc.record_match_result("R1M2", "P03", "P04", "P04")
        calc.record_match_result("R2M1", "P01", "P03", "P03")
        calc.record_match_result("R2M2", "P02", "P04", "P02")
        calc.record_match_result("R3M1", "P01", "P04", "P04")
        calc.record_match_result("R3M2", "P02", "P03", "P03")

        standings = calc.get_standings()

        # Verify results
        assert len(standings) == 4

        # P03 and P04 both have 6 points (2 wins each)
        p03 = next(s for s in standings if s.player_id == "P03")
        p04 = next(s for s in standings if s.player_id == "P04")

        assert p03.points == 6
        assert p04.points == 6

        # P04 beat P03 head-to-head, should rank higher
        assert p04.rank < p03.rank

        # Verify match tracker has all results
        assert len(tracker.get_all_matches()) == 6
