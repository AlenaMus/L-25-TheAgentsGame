"""
MCP Tool Handlers for Player Agent.

Implements the three required tools:
- handle_game_invitation: Accept/reject game invitations
- choose_parity: Make even/odd choice
- notify_match_result: Receive match results
"""

from player_agent.handlers.invitation import handle_game_invitation
from player_agent.handlers.choice import choose_parity
from player_agent.handlers.result import notify_match_result

__all__ = [
    "handle_game_invitation",
    "choose_parity",
    "notify_match_result"
]
