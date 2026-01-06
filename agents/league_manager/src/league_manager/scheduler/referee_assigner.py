"""
Referee assignment logic.

Assigns referees to matches in round-robin fashion.
"""

from typing import List, Dict, Tuple


def assign_referees_to_matches(
    schedule: List[List[Tuple[str, str]]], 
    referees: List[Dict]
) -> List[List[Dict]]:
    """
    Assign referees to matches.
    
    Simple round-robin assignment of referees to matches.
    
    Args:
        schedule: List of rounds (each round is list of match tuples)
        referees: List of referee dictionaries
        
    Returns:
        List of rounds with referee assignments
        
    Example:
        >>> schedule = [[("P01", "P02"), ("P03", "P04")]]
        >>> referees = [{"referee_id": "REF01", "endpoint": "..."}]
        >>> assigned = assign_referees_to_matches(schedule, referees)
        >>> assigned[0][0]["referee_id"]
        'REF01'
    """
    if not referees:
        raise ValueError("No referees available")
    
    referee_idx = 0
    assigned_schedule = []
    
    for round_matches in schedule:
        round_data = []
        for match in round_matches:
            # Assign next available referee (round-robin)
            referee = referees[referee_idx % len(referees)]
            referee_idx += 1
            
            round_data.append({
                "player_A_id": match[0],
                "player_B_id": match[1],
                "referee_id": referee["referee_id"],
                "referee_endpoint": referee["endpoint"]
            })
        
        assigned_schedule.append(round_data)
    
    return assigned_schedule
