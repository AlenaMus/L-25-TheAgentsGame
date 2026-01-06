"""
Match result reporting handler.

Handles MATCH_RESULT_REPORT messages from referees.
Updates standings and checks for round completion.
"""

from datetime import datetime, timezone
from typing import Dict, Optional

from league_manager.standings import StandingsCalculator
from league_manager.handlers.round_manager import RoundManager
from league_manager.utils.logger import logger


async def handle_match_result_report(
    params: Dict,
    standings_calculator: StandingsCalculator,
    round_manager: RoundManager,
    league_id: str
) -> Dict:
    """
    Handle match result report from referee.

    Args:
        params: Request parameters containing match result
        standings_calculator: Standings calculator instance
        round_manager: Round manager instance
        league_id: League identifier

    Returns:
        Acknowledgment response

    Message Flow:
        Request: MATCH_RESULT_REPORT (from referee)
        Response: Acknowledgment
        Side Effect: Updates standings, checks round completion

    Example Request:
        {
            "protocol": "league.v2",
            "message_type": "MATCH_RESULT_REPORT",
            "sender": "referee:REF01",
            "timestamp": "2025-01-15T10:30:00Z",
            "conversation_id": "conv_match_r1m1_result",
            "league_id": "league_2025_even_odd",
            "round_id": 1,
            "match_id": "R1M1",
            "game_type": "even_odd",
            "result": {
                "winner": "P01",
                "score": {"P01": 3, "P02": 0},
                "details": {
                    "drawn_number": 8,
                    "choices": {"P01": "even", "P02": "odd"}
                }
            }
        }
    """
    logger.info("Match result report received", params=params)

    # Extract match information
    match_id = params.get("match_id")
    round_id = params.get("round_id")
    result = params.get("result", {})
    winner_id = result.get("winner")
    score = result.get("score", {})

    # Validate required fields
    if not match_id or not round_id:
        logger.warning("Invalid result report: missing match_id or round_id")
        return _create_error_response(
            params,
            "Missing required fields: match_id or round_id"
        )

    # Extract player IDs from score
    player_ids = list(score.keys())
    if len(player_ids) != 2:
        logger.warning("Invalid result report: score must have 2 players")
        return _create_error_response(
            params,
            "Invalid score: must contain exactly 2 players"
        )

    player_a_id = player_ids[0]
    player_b_id = player_ids[1]

    # Update standings
    try:
        standings_calculator.record_match_result(
            match_id=match_id,
            player_a_id=player_a_id,
            player_b_id=player_b_id,
            winner_id=winner_id
        )
        logger.info(
            "Standings updated",
            match_id=match_id,
            winner=winner_id or "TIE"
        )
    except Exception as e:
        logger.error(
            "Failed to update standings",
            error=str(e),
            match_id=match_id
        )
        return _create_error_response(params, f"Standings update failed: {e}")

    # Mark match as complete and check round completion
    round_complete = round_manager.mark_match_complete(match_id, round_id)

    if round_complete:
        logger.info(
            "Round complete detected",
            round_id=round_id,
            match_id=match_id
        )
        # Note: Actual round completion message broadcast handled by caller

    # Create acknowledgment response
    response = {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_ACK",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conversation_id": params.get("conversation_id", "conv_unknown"),
        "acknowledged": True,
        "match_id": match_id,
        "round_complete": round_complete
    }

    logger.info(
        "Match result acknowledged",
        match_id=match_id,
        round_complete=round_complete
    )

    return response


def _create_error_response(params: Dict, reason: str) -> Dict:
    """Create error acknowledgment response."""
    return {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_ACK",
        "sender": "league_manager",
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "conversation_id": params.get("conversation_id", "conv_unknown"),
        "acknowledged": False,
        "error": reason
    }


__all__ = ["handle_match_result_report"]
