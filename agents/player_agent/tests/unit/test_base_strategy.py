"""
Unit tests for base Strategy class.

Tests the abstract Strategy interface including:
- Abstract method enforcement
- get_name method
- Interface contract
"""

import pytest
from abc import ABC

from player_agent.strategies.base import Strategy


def test_strategy_is_abstract():
    """
    Test that Strategy is an abstract base class.

    Arrange: Check Strategy class
    Act: Verify it's an ABC
    Assert: Inherits from ABC
    """
    assert issubclass(Strategy, ABC)


def test_strategy_cannot_be_instantiated():
    """
    Test that Strategy cannot be instantiated directly.

    Arrange: Try to create Strategy instance
    Act: Call Strategy()
    Assert: Raises TypeError
    """
    with pytest.raises(TypeError):
        Strategy()


def test_strategy_requires_choose_parity_implementation():
    """
    Test that concrete strategy must implement choose_parity.

    Arrange: Create incomplete concrete class
    Act: Try to instantiate
    Assert: Raises TypeError
    """
    class IncompleteStrategy(Strategy):
        pass

    with pytest.raises(TypeError):
        IncompleteStrategy()


def test_strategy_concrete_implementation_works():
    """
    Test that complete concrete strategy can be instantiated.

    Arrange: Create complete concrete class
    Act: Instantiate it
    Assert: Works without error
    """
    class ConcreteStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "even"

    strategy = ConcreteStrategy()
    assert isinstance(strategy, Strategy)


def test_strategy_get_name_returns_class_name():
    """
    Test that get_name returns correct class name.

    Arrange: Create concrete strategy
    Act: Call get_name
    Assert: Returns class name
    """
    class TestStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "odd"

    strategy = TestStrategy()
    assert strategy.get_name() == "TestStrategy"


def test_strategy_choose_parity_signature():
    """
    Test that choose_parity has correct signature.

    Arrange: Create concrete strategy
    Act: Call with correct parameters
    Assert: Works correctly
    """
    class MyStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "even"

    strategy = MyStrategy()
    result = strategy.choose_parity(
        match_id="M1",
        opponent_id="P02",
        opponent_history=[],
        standings={}
    )

    assert result == "even"


def test_strategy_choose_parity_parameters():
    """
    Test that choose_parity receives all parameters.

    Arrange: Create strategy that checks params
    Act: Call with specific parameters
    Assert: All parameters received
    """
    class ParamCheckStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            assert match_id == "TEST_MATCH"
            assert opponent_id == "P99"
            assert opponent_history == [{"test": "data"}]
            assert standings == {"wins": 5}
            return "odd"

    strategy = ParamCheckStrategy()
    result = strategy.choose_parity(
        match_id="TEST_MATCH",
        opponent_id="P99",
        opponent_history=[{"test": "data"}],
        standings={"wins": 5}
    )

    assert result == "odd"


def test_strategy_multiple_implementations():
    """
    Test that multiple concrete strategies can coexist.

    Arrange: Create two different strategies
    Act: Instantiate both
    Assert: Both work independently
    """
    class EvenStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "even"

    class OddStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "odd"

    even_strat = EvenStrategy()
    odd_strat = OddStrategy()

    assert even_strat.choose_parity("M1", "P02", [], {}) == "even"
    assert odd_strat.choose_parity("M1", "P02", [], {}) == "odd"


def test_strategy_get_name_different_classes():
    """
    Test that get_name returns different names for different classes.

    Arrange: Create two strategy classes
    Act: Call get_name on each
    Assert: Names are different
    """
    class StrategyA(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "even"

    class StrategyB(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "odd"

    strat_a = StrategyA()
    strat_b = StrategyB()

    assert strat_a.get_name() == "StrategyA"
    assert strat_b.get_name() == "StrategyB"
    assert strat_a.get_name() != strat_b.get_name()


def test_strategy_can_access_opponent_history():
    """
    Test that concrete strategy can access opponent_history.

    Arrange: Create strategy that uses history
    Act: Call with history data
    Assert: History is accessible
    """
    class HistoryStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            if opponent_history and len(opponent_history) > 0:
                return "even"
            return "odd"

    strategy = HistoryStrategy()

    # With empty history
    assert strategy.choose_parity("M1", "P02", [], {}) == "odd"

    # With history
    history = [{"match": "M1", "choice": "even"}]
    assert strategy.choose_parity("M2", "P02", history, {}) == "even"


def test_strategy_can_access_standings():
    """
    Test that concrete strategy can access standings.

    Arrange: Create strategy that uses standings
    Act: Call with standings data
    Assert: Standings are accessible
    """
    class StandingsStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            if standings.get("wins", 0) > 5:
                return "even"
            return "odd"

    strategy = StandingsStrategy()

    # With low wins
    assert strategy.choose_parity("M1", "P02", [], {"wins": 2}) == "odd"

    # With high wins
    assert strategy.choose_parity("M1", "P02", [], {"wins": 10}) == "even"


def test_strategy_inheritance_chain():
    """
    Test that strategy inheritance works correctly.

    Arrange: Create multi-level inheritance
    Act: Instantiate leaf class
    Assert: Works correctly
    """
    class BaseCustomStrategy(Strategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "even"

    class DerivedStrategy(BaseCustomStrategy):
        def choose_parity(self, match_id, opponent_id, opponent_history, standings):
            return "odd"

    strategy = DerivedStrategy()
    assert isinstance(strategy, Strategy)
    assert strategy.choose_parity("M1", "P02", [], {}) == "odd"
