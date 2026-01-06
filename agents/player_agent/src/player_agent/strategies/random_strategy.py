"""
Random strategy implementation.

Implements a 50/50 random choice strategy - the Nash Equilibrium
for the Even/Odd game. This strategy cannot be exploited and
provides a safe baseline with expected 50% win rate.
"""

import random
from typing import List, Dict

from player_agent.strategies.base import Strategy
from player_agent.utils.logger import logger


class RandomStrategy(Strategy):
    """
    Random 50/50 strategy (baseline).

    Game Theory Properties:
    - Nash Equilibrium strategy for Even/Odd game
    - Expected win rate: 50% against any opponent
    - Cannot be exploited (no pattern to detect)
    - Unexploitable baseline

    Performance:
    - Computation time: < 1ms
    - Memory usage: O(1)
    - No data requirements

    Use Cases:
    - Week 1: Infrastructure testing
    - Against unknown opponents: Safe baseline
    - As fallback: If other strategies fail
    """

    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """
        Choose randomly between "even" and "odd" with 50% probability each.

        This implementation ignores opponent_history and standings since
        random strategy doesn't require any contextual information.

        Args:
            match_id: Current match ID (for logging).
            opponent_id: Opponent player ID (for logging).
            opponent_history: Unused in random strategy.
            standings: Unused in random strategy.

        Returns:
            str: "even" or "odd" with equal probability.
        """
        choice = random.choice(["even", "odd"])

        logger.debug(
            "Random choice made",
            match_id=match_id,
            opponent_id=opponent_id,
            choice=choice,
            strategy=self.get_name()
        )

        return choice
