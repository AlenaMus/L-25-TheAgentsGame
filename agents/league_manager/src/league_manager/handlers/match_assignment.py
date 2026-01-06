"""
Match assignment handler.

Returns matches assigned to a specific referee.
"""

from typing import Dict


async def get_assigned_matches(params: Dict, league_store) -> Dict:
    """
    Get matches assigned to a specific referee.

    Args:
        params: Request parameters with referee_id
        league_store: League data store

    Returns:
        List of assigned matches

    Example:
        >>> result = await get_assigned_matches({"referee_id": "REF01"}, store)
        >>> matches = result["matches"]
    """
    referee_id = params.get("referee_id")
    schedule = league_store.load_schedule()

    if not schedule:
        return {"matches": []}

    # Find all matches assigned to this referee
    assigned_matches = []
    for round_idx, round_matches in enumerate(schedule):
        for match_idx, match in enumerate(round_matches):
            if match.get("referee_id") == referee_id:
                match_id = f"R{round_idx + 1}M{match_idx + 1}"
                assigned_matches.append({
                    "match_id": match_id,
                    "round": round_idx + 1,
                    "player_A_id": match["player_A_id"],
                    "player_B_id": match["player_B_id"],
                    "status": match.get("status", "PENDING")
                })

    return {"matches": assigned_matches}
