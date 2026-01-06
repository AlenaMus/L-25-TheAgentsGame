"""
Unit tests for RandomStrategy.

Tests the random parity choice strategy including:
- 50/50 distribution
- Valid output ("even" or "odd")
- Statistical properties
- Independence from context
"""

import pytest
from collections import Counter

from player_agent.strategies.random_strategy import RandomStrategy


@pytest.fixture
def strategy():
    """Create RandomStrategy instance for testing."""
    return RandomStrategy()


def test_random_strategy_returns_valid_choice(strategy):
    """
    Test that strategy returns either "even" or "odd".

    Arrange: Create RandomStrategy
    Act: Call choose_parity
    Assert: Result is "even" or "odd"
    """
    result = strategy.choose_parity(
        match_id="test_match",
        opponent_id="P02",
        opponent_history=[],
        standings={}
    )

    assert result in ["even", "odd"]


def test_random_strategy_get_name(strategy):
    """
    Test that strategy returns correct name.

    Arrange: Create RandomStrategy
    Act: Call get_name
    Assert: Returns "RandomStrategy"
    """
    assert strategy.get_name() == "RandomStrategy"


def test_random_strategy_ignores_opponent_history(strategy):
    """
    Test that strategy ignores opponent history.

    Arrange: Create strategy with varied opponent history
    Act: Call choose_parity multiple times
    Assert: Still produces valid choices
    """
    opponent_history = [
        {"match_id": "M1", "opponent_choice": "even"},
        {"match_id": "M2", "opponent_choice": "even"},
        {"match_id": "M3", "opponent_choice": "even"}
    ]

    result = strategy.choose_parity(
        match_id="test",
        opponent_id="P02",
        opponent_history=opponent_history,
        standings={}
    )

    assert result in ["even", "odd"]


def test_random_strategy_ignores_standings(strategy):
    """
    Test that strategy ignores tournament standings.

    Arrange: Create strategy with standings data
    Act: Call choose_parity
    Assert: Returns valid choice regardless of standings
    """
    standings = {
        "wins": 10,
        "losses": 2,
        "draws": 1,
        "points": 31
    }

    result = strategy.choose_parity(
        match_id="test",
        opponent_id="P02",
        opponent_history=[],
        standings=standings
    )

    assert result in ["even", "odd"]


def test_random_strategy_statistical_distribution(strategy):
    """
    Test that strategy produces roughly 50/50 distribution.

    Arrange: Create strategy
    Act: Generate 1000 choices
    Assert: Distribution is within acceptable bounds (40-60%)
    """
    choices = []
    for i in range(1000):
        choice = strategy.choose_parity(
            match_id=f"match_{i}",
            opponent_id="P02",
            opponent_history=[],
            standings={}
        )
        choices.append(choice)

    counts = Counter(choices)
    even_count = counts["even"]
    odd_count = counts["odd"]

    # With 1000 samples, expect 400-600 range (very loose bounds)
    assert 400 <= even_count <= 600
    assert 400 <= odd_count <= 600
    assert even_count + odd_count == 1000


def test_random_strategy_tighter_distribution(strategy):
    """
    Test tighter distribution bounds with more samples.

    Arrange: Create strategy
    Act: Generate 10000 choices
    Assert: Distribution is within tighter bounds (48-52%)
    """
    choices = []
    for i in range(10000):
        choice = strategy.choose_parity(
            match_id=f"match_{i}",
            opponent_id="P02",
            opponent_history=[],
            standings={}
        )
        choices.append(choice)

    counts = Counter(choices)
    even_ratio = counts["even"] / len(choices)

    # With 10000 samples, expect very close to 50%
    assert 0.48 <= even_ratio <= 0.52


def test_random_strategy_multiple_instances_independent():
    """
    Test that multiple strategy instances are independent.

    Arrange: Create two strategy instances
    Act: Generate choices from both
    Assert: Both produce valid choices
    """
    strategy1 = RandomStrategy()
    strategy2 = RandomStrategy()

    choice1 = strategy1.choose_parity("test", "P02", [], {})
    choice2 = strategy2.choose_parity("test", "P02", [], {})

    assert choice1 in ["even", "odd"]
    assert choice2 in ["even", "odd"]


def test_random_strategy_with_empty_params(strategy):
    """
    Test strategy with minimal/empty parameters.

    Arrange: Create strategy
    Act: Call with empty lists and dicts
    Assert: Still produces valid choice
    """
    result = strategy.choose_parity(
        match_id="",
        opponent_id="",
        opponent_history=[],
        standings={}
    )

    assert result in ["even", "odd"]


def test_random_strategy_consecutive_calls_vary(strategy):
    """
    Test that consecutive calls can produce different results.

    Arrange: Create strategy
    Act: Call choose_parity 100 times
    Assert: At least one "even" and one "odd" appear
    """
    choices = set()
    for i in range(100):
        choice = strategy.choose_parity(
            match_id=f"match_{i}",
            opponent_id="P02",
            opponent_history=[],
            standings={}
        )
        choices.add(choice)

    # With 100 calls, extremely unlikely to get only one choice
    assert "even" in choices
    assert "odd" in choices


def test_random_strategy_same_match_id_different_results():
    """
    Test that same match_id can produce different results.

    Arrange: Create strategy
    Act: Call with same match_id multiple times
    Assert: Results vary (not deterministic based on match_id)
    """
    strategy = RandomStrategy()
    choices = set()

    for _ in range(50):
        choice = strategy.choose_parity(
            match_id="same_match_id",
            opponent_id="P02",
            opponent_history=[],
            standings={}
        )
        choices.add(choice)

        # If we've seen both choices, test passes
        if len(choices) == 2:
            break

    # Should see variation even with same match_id
    assert len(choices) == 2


def test_random_strategy_no_bias_towards_even(strategy):
    """
    Test that there's no systematic bias towards "even".

    Arrange: Create strategy
    Act: Generate 500 choices
    Assert: "even" count is within 40-60% range
    """
    choices = [
        strategy.choose_parity(f"match_{i}", "P02", [], {})
        for i in range(500)
    ]

    even_count = choices.count("even")
    even_ratio = even_count / len(choices)

    assert 0.4 <= even_ratio <= 0.6


def test_random_strategy_no_bias_towards_odd(strategy):
    """
    Test that there's no systematic bias towards "odd".

    Arrange: Create strategy
    Act: Generate 500 choices
    Assert: "odd" count is within 40-60% range
    """
    choices = [
        strategy.choose_parity(f"match_{i}", "P02", [], {})
        for i in range(500)
    ]

    odd_count = choices.count("odd")
    odd_ratio = odd_count / len(choices)

    assert 0.4 <= odd_ratio <= 0.6


def test_random_strategy_with_none_standings(strategy):
    """
    Test handling when standings is None.

    Arrange: Create strategy
    Act: Call with None standings
    Assert: Still produces valid choice
    """
    result = strategy.choose_parity(
        match_id="test",
        opponent_id="P02",
        opponent_history=[],
        standings=None
    )

    assert result in ["even", "odd"]


def test_random_strategy_with_none_history(strategy):
    """
    Test handling when opponent_history is None.

    Arrange: Create strategy
    Act: Call with None history
    Assert: Still produces valid choice
    """
    result = strategy.choose_parity(
        match_id="test",
        opponent_id="P02",
        opponent_history=None,
        standings={}
    )

    assert result in ["even", "odd"]
