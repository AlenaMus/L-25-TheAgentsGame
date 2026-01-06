"""
Unit tests for round-robin scheduler.
"""

import pytest
from league_manager.scheduler.round_robin import create_round_robin_schedule
from league_manager.scheduler.referee_assigner import assign_referees_to_matches


def test_round_robin_4_players():
    """Test round-robin schedule with 4 players."""
    player_ids = ["P01", "P02", "P03", "P04"]
    schedule = create_round_robin_schedule(player_ids)
    
    # 4 players = 3 rounds
    assert len(schedule) == 3
    
    # Total matches = 6 (4 choose 2)
    total_matches = sum(len(round_matches) for round_matches in schedule)
    assert total_matches == 6
    
    # Each player plays 3 times
    player_match_count = {pid: 0 for pid in player_ids}
    for round_matches in schedule:
        for match in round_matches:
            player_match_count[match[0]] += 1
            player_match_count[match[1]] += 1
    
    for count in player_match_count.values():
        assert count == 3


def test_round_robin_3_players():
    """Test round-robin schedule with 3 players (odd)."""
    player_ids = ["P01", "P02", "P03"]
    schedule = create_round_robin_schedule(player_ids)
    
    # 3 players = 3 rounds
    assert len(schedule) == 3
    
    # Total matches = 3 (3 choose 2)
    total_matches = sum(len(round_matches) for round_matches in schedule)
    assert total_matches == 3


def test_referee_assignment():
    """Test referee assignment to matches."""
    schedule = [[("P01", "P02"), ("P03", "P04")]]
    referees = [
        {"referee_id": "REF01", "endpoint": "http://localhost:8001/mcp"}
    ]
    
    assigned = assign_referees_to_matches(schedule, referees)
    
    assert len(assigned) == 1
    assert len(assigned[0]) == 2
    assert assigned[0][0]["referee_id"] == "REF01"
    assert assigned[0][0]["player_A_id"] == "P01"
    assert assigned[0][0]["player_B_id"] == "P02"
