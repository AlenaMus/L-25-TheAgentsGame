"""
League query handlers.

Handles get_standings and start_league queries.
"""

from typing import Dict
from ..utils.logger import logger
from ..scheduler.match_scheduler import MatchScheduler


async def get_standings(standings_calc) -> Dict:
    """
    Get current standings.
    
    Args:
        standings_calc: Standings calculator
        
    Returns:
        Current standings
    """
    standings = standings_calc.get_standings()
    
    return {
        "protocol": "league.v2",
        "message_type": "STANDINGS_UPDATE",
        "league_id": "league_2025_even_odd",
        "standings": standings
    }


async def start_league(agent_registry, league_store) -> Dict:
    """
    Start the league tournament.

    Creates round-robin schedule and assigns referees.

    Args:
        agent_registry: Agent registry
        league_store: League data store

    Returns:
        League start confirmation
    """
    # Get all players
    players = agent_registry.get_all_players()
    player_ids = [p["player_id"] for p in players]

    # Get all referees
    referees = agent_registry.get_all_referees()

    # Create scheduler and generate matches
    league_id = "league_2025_even_odd"
    scheduler = MatchScheduler(league_id=league_id)
    tournament_schedule = scheduler.create_tournament_schedule(player_ids, referees)

    # Convert Match objects to dict and add referee endpoint
    schedule_dict = []
    for round_matches in tournament_schedule:
        round_dict = []
        for match in round_matches:
            match_dict = match.to_dict(league_id=league_id)
            # Find referee endpoint
            referee = next((r for r in referees if r["referee_id"] == match.referee_id), None)
            if referee:
                match_dict["referee_endpoint"] = referee["endpoint"]
            round_dict.append(match_dict)
        schedule_dict.append(round_dict)

    # Save schedule
    league_store.save_schedule(schedule_dict)

    logger.info(
        "League started",
        num_players=len(player_ids),
        num_rounds=len(tournament_schedule),
        num_referees=len(referees)
    )

    return {
        "protocol": "league.v2",
        "message_type": "LEAGUE_START_RESPONSE",
        "status": "STARTED",
        "success": True,
        "schedule": schedule_dict,
        "total_rounds": len(tournament_schedule)
    }
