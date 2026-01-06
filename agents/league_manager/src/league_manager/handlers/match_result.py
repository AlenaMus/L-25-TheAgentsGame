"""
Match result handler.

Handles MATCH_RESULT_REPORT from referees.
"""

from typing import Dict
from ..utils.logger import logger


async def report_match_result(params: Dict, standings_calc, league_store) -> Dict:
    """
    Handle match result report from referee.

    Args:
        params: Match result parameters
        standings_calc: Standings calculator
        league_store: League data store

    Returns:
        Acknowledgment

    Example:
        >>> result = await report_match_result(params, calc, store)
        >>> assert result["status"] == "RECORDED"
    """
    match_id = params.get("match_id")
    players = params.get("players", {})

    # Update standings for each player
    for player_id, player_result in players.items():
        result_type = player_result.get("result")
        points = player_result.get("points", 0)

        if result_type == "WIN":
            standings_calc.record_win(player_id)
        elif result_type == "LOSS":
            standings_calc.record_loss(player_id)
        elif result_type == "TIE":
            standings_calc.record_draw(player_id)

    # Save standings
    standings = standings_calc.get_standings()
    league_store.save_standings(standings)

    # ✅ FIX: Mark match as completed in schedule
    # Parse match_id (format: "league_2025_even_odd_R1_M001")
    try:
        parts = match_id.split("_")
        round_part = [p for p in parts if p.startswith("R")][0]
        match_part = [p for p in parts if p.startswith("M")][0]
        round_idx = int(round_part[1:]) - 1  # Convert to 0-based
        match_idx = int(match_part[1:]) - 1  # Convert to 0-based
        league_store.update_match_status(round_idx, match_idx, "COMPLETED")
        logger.debug("Match marked as completed", match_id=match_id, round=round_idx+1, match=match_idx+1)
    except (IndexError, ValueError) as e:
        logger.warning("Failed to parse match_id for status update", match_id=match_id, error=str(e))

    logger.info(
        "Match result recorded",
        match_id=match_id,
        players=list(players.keys())
    )

    return {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_ACK",
        "match_id": match_id,
        "status": "RECORDED",
        "standings_updated": True
    }
