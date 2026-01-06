"""
Round-robin tournament scheduler.

Generates fair round-robin schedule where every player plays every other player once.
"""

from itertools import combinations
from typing import List, Tuple


def create_round_robin_schedule(player_ids: List[str]) -> List[List[Tuple[str, str]]]:
    """
    Create round-robin schedule for all players.
    
    Each player plays every other player exactly once.
    Matches distributed across rounds (no player plays twice in same round).
    
    Args:
        player_ids: List of player IDs
        
    Returns:
        List of rounds, each round is list of matches (tuples)
        
    Example:
        >>> schedule = create_round_robin_schedule(["P01", "P02", "P03", "P04"])
        >>> len(schedule)  # 3 rounds for 4 players
        3
        >>> len(schedule[0])  # 2 matches in round 1
        2
    """
    n = len(player_ids)
    if n < 2:
        return []
    
    # Generate all possible pairings
    all_matches = list(combinations(player_ids, 2))
    
    # Calculate number of rounds
    num_rounds = n - 1 if n % 2 == 0 else n
    
    # Initialize rounds
    rounds = [[] for _ in range(num_rounds)]
    
    # Assign matches to rounds
    for match in all_matches:
        # Find first round where neither player is already playing
        for round_idx in range(num_rounds):
            players_in_round = set()
            for m in rounds[round_idx]:
                players_in_round.add(m[0])
                players_in_round.add(m[1])
            
            # Check if both players are free
            if match[0] not in players_in_round and match[1] not in players_in_round:
                rounds[round_idx].append(match)
                break
    
    return rounds
