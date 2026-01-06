"""
Base strategy interface for player agents.

Defines the abstract Strategy pattern for implementing different
game-playing strategies (random, adaptive, LLM-based).
"""

from abc import ABC, abstractmethod
from typing import List, Dict


class Strategy(ABC):
    """
    Base class for all player strategies.

    All concrete strategies must implement the choose_parity method
    which returns either "even" or "odd" based on game context.

    The strategy pattern allows for pluggable decision-making logic
    without changing the handler code.
    """

    @abstractmethod
    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """
        Choose parity for this match.

        Args:
            match_id: Current match ID (for logging/tracking).
            opponent_id: Opponent player ID.
            opponent_history: List of past matches against this opponent.
                Format: [
                    {
                        "match_id": "R1M1",
                        "opponent_choice": "even",
                        "drawn_number": 8,
                        "won": True
                    },
                    ...
                ]
            standings: Current tournament standings.
                Format: {
                    "wins": 2,
                    "losses": 1,
                    "draws": 0,
                    "points": 7
                }

        Returns:
            str: "even" or "odd"

        Raises:
            ValueError: If implementation returns invalid choice.
        """
        pass

    def get_name(self) -> str:
        """
        Return strategy name for logging.

        Returns:
            str: Strategy class name (e.g., "RandomStrategy").
        """
        return self.__class__.__name__
