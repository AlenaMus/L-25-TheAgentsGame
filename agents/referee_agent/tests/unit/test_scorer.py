"""
Unit tests for winner determination logic.

Tests score calculation and winner selection.
"""

import pytest
from referee.game_logic import determine_winner


def test_determine_winner_even_number():
    """Test winner determination with even drawn number."""
    choices = {"P01": "even", "P02": "odd"}
    result = determine_winner(8, choices)

    assert result["status"] == "WIN"
    assert result["winner_player_id"] == "P01"
    assert result["drawn_number"] == 8
    assert result["number_parity"] == "even"
    assert result["scores"]["P01"] == 3
    assert result["scores"]["P02"] == 0


def test_determine_winner_odd_number():
    """Test winner determination with odd drawn number."""
    choices = {"P01": "even", "P02": "odd"}
    result = determine_winner(7, choices)

    assert result["status"] == "WIN"
    assert result["winner_player_id"] == "P02"
    assert result["drawn_number"] == 7
    assert result["number_parity"] == "odd"
    assert result["scores"]["P01"] == 0
    assert result["scores"]["P02"] == 3


def test_determine_winner_all_parities():
    """Test all numbers 1-10 produce correct parity."""
    even_nums = [2, 4, 6, 8, 10]
    odd_nums = [1, 3, 5, 7, 9]

    for num in even_nums:
        result = determine_winner(num, {"P01": "even", "P02": "odd"})
        assert result["number_parity"] == "even"
        assert result["winner_player_id"] == "P01"

    for num in odd_nums:
        result = determine_winner(num, {"P01": "even", "P02": "odd"})
        assert result["number_parity"] == "odd"
        assert result["winner_player_id"] == "P02"


def test_determine_winner_both_choose_same():
    """Test when both players choose same parity."""
    # Both choose even, drawn number is even
    choices = {"P01": "even", "P02": "even"}
    result = determine_winner(8, choices)

    # First player in dict wins (arbitrary but consistent)
    assert result["winner_player_id"] == "P01"
    assert result["scores"]["P01"] == 3
    assert result["scores"]["P02"] == 0

    # Both choose odd, drawn number is odd
    choices = {"P01": "odd", "P02": "odd"}
    result = determine_winner(7, choices)

    assert result["winner_player_id"] == "P01"
    assert result["scores"]["P01"] == 3
    assert result["scores"]["P02"] == 0
