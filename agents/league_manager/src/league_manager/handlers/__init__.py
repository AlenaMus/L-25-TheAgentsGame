"""Handler modules for MCP tools."""

from .player_registration import register_player
from .referee_registration import register_referee
from .match_result import report_match_result
from .league_query import get_standings, start_league
from .match_assignment import get_assigned_matches

__all__ = [
    "register_player",
    "register_referee",
    "report_match_result",
    "get_standings",
    "start_league",
    "get_assigned_matches",
]
