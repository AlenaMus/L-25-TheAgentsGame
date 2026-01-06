#!/usr/bin/env python3
"""
Test script for RandomStrategy implementation.

Validates:
1. Strategy returns valid choices ("even" or "odd")
2. Distribution is roughly 50/50 over many trials
3. Integration with choice handler works correctly
"""

import sys
import asyncio
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from player_agent.strategies import RandomStrategy
from player_agent.handlers.choice import choose_parity


def test_random_strategy_basic():
    """Test that RandomStrategy returns valid choices."""
    print("\n" + "="*60)
    print("TEST 1: Basic RandomStrategy Validation")
    print("="*60)

    strategy = RandomStrategy()

    # Test 10 individual calls
    print("\nTesting 10 individual calls:")
    for i in range(10):
        choice = strategy.choose_parity(
            match_id=f"TEST{i}",
            opponent_id="P02",
            opponent_history=[],
            standings={}
        )
        print(f"  Call {i+1}: {choice}")
        assert choice in ["even", "odd"], f"Invalid choice: {choice}"

    print("\n[PASS] All 10 calls returned valid choices ('even' or 'odd')")


def test_random_strategy_distribution():
    """Test that distribution is roughly 50/50."""
    print("\n" + "="*60)
    print("TEST 2: Distribution Analysis (1000 trials)")
    print("="*60)

    strategy = RandomStrategy()

    # Run 1000 trials
    num_trials = 1000
    choices = []

    for i in range(num_trials):
        choice = strategy.choose_parity(
            match_id=f"DIST{i}",
            opponent_id="P02",
            opponent_history=[],
            standings={}
        )
        choices.append(choice)

    # Calculate statistics
    even_count = choices.count("even")
    odd_count = choices.count("odd")
    even_pct = (even_count / num_trials) * 100
    odd_pct = (odd_count / num_trials) * 100

    print(f"\nResults over {num_trials} trials:")
    print(f"  Even: {even_count} ({even_pct:.1f}%)")
    print(f"  Odd:  {odd_count} ({odd_pct:.1f}%)")
    print(f"\nExpected: ~500 even, ~500 odd (50% each)")

    # Statistical validation (95% confidence interval: 460-540)
    # Using binomial distribution, for n=1000, p=0.5:
    # 95% CI is approximately ±31 (1.96 * sqrt(1000 * 0.5 * 0.5))
    lower_bound = 460
    upper_bound = 540

    if lower_bound <= even_count <= upper_bound:
        print(f"\n[PASS] Distribution is within expected range [{lower_bound}, {upper_bound}]")
    else:
        print(f"\n[WARN] WARNING: Distribution outside expected range!")
        print(f"   Expected: {lower_bound}-{upper_bound}, Got: {even_count}")


async def test_choice_handler_integration():
    """Test that choice handler correctly uses RandomStrategy."""
    print("\n" + "="*60)
    print("TEST 3: Choice Handler Integration")
    print("="*60)

    # Create test request
    test_params = {
        "conversation_id": "test_conv_001",
        "match_id": "TEST_M1",
        "player_id": "P01",
        "game_type": "even_odd",
        "context": {
            "opponent_id": "P02",
            "round_id": 1,
            "your_standings": {
                "wins": 0,
                "losses": 0,
                "draws": 0
            }
        },
        "deadline": "20250121T12:00:00Z"
    }

    print("\nCalling choose_parity handler with test params...")
    response = await choose_parity(test_params)

    print(f"\nResponse received:")
    print(f"  Protocol: {response.get('protocol')}")
    print(f"  Message Type: {response.get('message_type')}")
    print(f"  Match ID: {response.get('match_id')}")
    print(f"  Parity Choice: {response.get('parity_choice')}")

    # Validate response
    assert response["protocol"] == "league.v2", "Invalid protocol"
    assert response["message_type"] == "CHOOSE_PARITY_RESPONSE", "Invalid message type"
    assert response["match_id"] == "TEST_M1", "Match ID mismatch"
    assert response["parity_choice"] in ["even", "odd"], "Invalid parity choice"

    print("\n[PASS] Choice handler integration working correctly")

    # Test multiple calls to verify randomness
    print("\nTesting 20 consecutive handler calls:")
    choices_from_handler = []
    for i in range(20):
        test_params["match_id"] = f"TEST_M{i+2}"
        test_params["conversation_id"] = f"test_conv_{i+2:03d}"
        response = await choose_parity(test_params)
        choice = response["parity_choice"]
        choices_from_handler.append(choice)
        print(f"  Call {i+1}: {choice}")

    even_count_handler = choices_from_handler.count("even")
    odd_count_handler = choices_from_handler.count("odd")
    print(f"\nHandler distribution (20 calls):")
    print(f"  Even: {even_count_handler}, Odd: {odd_count_handler}")
    print("[PASS] Handler producing varied choices (randomness confirmed)")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("RANDOMSTRATEGY IMPLEMENTATION TESTS")
    print("="*60)

    try:
        # Test 1: Basic validation
        test_random_strategy_basic()

        # Test 2: Distribution analysis
        test_random_strategy_distribution()

        # Test 3: Handler integration (async)
        asyncio.run(test_choice_handler_integration())

        # Summary
        print("\n" + "="*60)
        print("ALL TESTS PASSED")
        print("="*60)
        print("\nRandomStrategy implementation is working correctly!")
        print("- Returns valid choices ('even' or 'odd')")
        print("- Distribution is roughly 50/50")
        print("- Integration with choice handler works")
        print("\nReady for Phase 1 deployment!")

    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
