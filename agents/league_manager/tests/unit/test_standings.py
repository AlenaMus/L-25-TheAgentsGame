"""
Unit tests for standings calculator.
"""

import pytest
from league_manager.standings.calculator import StandingsCalculator


def test_add_player():
    """Test adding players to standings."""
    calc = StandingsCalculator()
    calc.add_player("P01", "Player 1")
    calc.add_player("P02", "Player 2")
    
    standings = calc.get_standings()
    assert len(standings) == 2


def test_record_win():
    """Test recording a win."""
    calc = StandingsCalculator()
    calc.add_player("P01", "Player 1")
    calc.record_win("P01")
    
    standings = calc.get_standings()
    assert standings[0]["wins"] == 1
    assert standings[0]["points"] == 3
    assert standings[0]["played"] == 1


def test_standings_sorting():
    """Test standings are sorted by points."""
    calc = StandingsCalculator()
    calc.add_player("P01", "Player 1")
    calc.add_player("P02", "Player 2")
    calc.add_player("P03", "Player 3")
    
    # P02 wins twice
    calc.record_win("P02")
    calc.record_win("P02")
    
    # P01 wins once
    calc.record_win("P01")
    
    standings = calc.get_standings()
    
    # P02 should be first (6 points)
    assert standings[0]["player_id"] == "P02"
    assert standings[0]["rank"] == 1
    assert standings[0]["points"] == 6
    
    # P01 should be second (3 points)
    assert standings[1]["player_id"] == "P01"
    assert standings[1]["rank"] == 2
    
    # P03 should be third (0 points)
    assert standings[2]["player_id"] == "P03"
    assert standings[2]["rank"] == 3
