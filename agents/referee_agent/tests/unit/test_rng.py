"""
Unit tests for random number generation.

Tests cryptographic random number generator.
"""

import pytest
from referee.game_logic import draw_number


def test_draw_number_in_range():
    """Test drawn number is always in range [1, 10]."""
    for _ in range(100):
        num = draw_number()
        assert 1 <= num <= 10
        assert isinstance(num, int)


def test_draw_number_distribution():
    """Test drawn numbers have reasonable distribution."""
    # Draw 1000 numbers
    draws = [draw_number() for _ in range(1000)]

    # Each number should appear roughly 100 times (10% of 1000)
    # Allow for statistical variance (50-150 appearances)
    for num in range(1, 11):
        count = draws.count(num)
        assert 50 < count < 150, f"Number {num} appeared {count} times"


def test_draw_number_produces_even_and_odd():
    """Test generator produces both even and odd numbers."""
    draws = [draw_number() for _ in range(100)]

    even_count = sum(1 for n in draws if n % 2 == 0)
    odd_count = sum(1 for n in draws if n % 2 == 1)

    # Both should be non-zero
    assert even_count > 0
    assert odd_count > 0

    # Should be roughly 50/50 (allow 30-70 split)
    assert 30 < even_count < 70
    assert 30 < odd_count < 70
