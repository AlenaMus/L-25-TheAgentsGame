"""
Winner determination logic for Even/Odd game.

Compares player choices to drawn number parity and
calculates match outcome.
"""

from typing import Dict, Optional


def determine_winner(
    drawn_number: int,
    choices: Dict[str, str]
) -> Dict:
    """
    Determine match winner based on drawn number and choices.

    Args:
        drawn_number: Random number drawn (1-10)
        choices: Dict of {player_id: "even" or "odd"}

    Returns:
        dict: Result containing:
            - status: "WIN"
            - winner_player_id: ID of winning player
            - drawn_number: The drawn number
            - number_parity: "even" or "odd"
            - choices: Player choices
            - scores: {player_id: points}

    Example:
        >>> choices = {"P01": "even", "P02": "odd"}
        >>> result = determine_winner(8, choices)
        >>> result["winner_player_id"]
        "P01"
    """
    # Determine parity of drawn number
    number_parity = "even" if drawn_number % 2 == 0 else "odd"

    # Find winner
    winner_id: Optional[str] = None
    for player_id, choice in choices.items():
        if choice == number_parity:
            winner_id = player_id
            break

    # Calculate scores (3 points for win, 0 for loss)
    scores = {}
    for player_id in choices.keys():
        scores[player_id] = 3 if player_id == winner_id else 0

    return {
        "status": "WIN",
        "winner_player_id": winner_id,
        "drawn_number": drawn_number,
        "number_parity": number_parity,
        "choices": choices,
        "scores": scores
    }
