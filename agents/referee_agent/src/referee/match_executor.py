"""
Match execution logic for Even/Odd game.

Orchestrates complete match flow from invitation to result reporting.
"""

from typing import Dict, Optional
from .mcp_client import MCPClient
from .utils.logger import logger
from .config import config
from .storage.agent_registry import AgentRegistry
from .game_logic import draw_number, determine_winner
from .handlers.notification import notify_players
from .handlers.league_reporter import report_to_league


class MatchExecutor:
    """
    Executes a single Even/Odd match.

    Handles invitation, move collection, winner determination,
    and result notification to players and league manager.
    """

    def __init__(self, agent_registry: AgentRegistry):
        """
        Initialize match executor.

        Args:
            agent_registry: Registry to look up player endpoints
        """
        self.agent_registry = agent_registry
        self.invitation_timeout = config.invitation_timeout
        self.choice_timeout = config.choice_timeout

    async def execute_match(self, match_data: Dict) -> bool:
        """
        Execute complete match flow.

        Args:
            match_data: Match info with match_id, player_A_id, player_B_id

        Returns:
            True if match completed successfully, False otherwise
        """
        match_id = match_data["match_id"]
        player_a_id = match_data["player_A_id"]
        player_b_id = match_data["player_B_id"]

        logger.info("Match started", match_id=match_id, player_A=player_a_id, player_B=player_b_id)

        try:
            # Step 1: Send invitations
            if not await self._send_invitations(match_data):
                return False

            # Step 2: Request moves from both players
            choice_a = await self._request_move(match_id, player_a_id, player_b_id)
            choice_b = await self._request_move(match_id, player_b_id, player_a_id)

            if not choice_a or not choice_b:
                logger.error("Move collection failed", match_id=match_id)
                return False

            # Step 3: Draw random number and determine winner
            drawn_number = draw_number()
            choices = {player_a_id: choice_a, player_b_id: choice_b}
            result = determine_winner(drawn_number, choices)

            logger.info(
                "Winner determined",
                match_id=match_id,
                winner=result["winner_player_id"],
                drawn_number=drawn_number,
                choices=choices
            )

            # Step 4: Notify players of result
            await notify_players(match_id, result, self.agent_registry)

            # Step 5: Report to League Manager
            await report_to_league(match_id, result)

            logger.info("Match completed", match_id=match_id)
            return True

        except Exception as e:
            logger.error("Match execution failed", match_id=match_id, error=str(e), exc_info=True)
            return False

    async def _send_invitations(self, match_data: Dict) -> bool:
        """Send game invitations to both players."""
        match_id = match_data["match_id"]
        player_a_id = match_data["player_A_id"]
        player_b_id = match_data["player_B_id"]
        league_id = match_data.get("league_id", "league_2025_even_odd")
        round_id = match_data.get("round_number", 1)

        client = MCPClient(timeout=self.invitation_timeout)
        try:
            player_a = self.agent_registry.get_player(player_a_id)
            player_b = self.agent_registry.get_player(player_b_id)

            if not player_a or not player_b:
                logger.error("Player not found", player_A=player_a_id, player_B=player_b_id)
                return False

            # Send invitations
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc).isoformat()
            conversation_id = f"conv_{match_id.lower().replace('_', '')}"

            resp_a = await client.call_tool(
                player_a["endpoint"],
                "handle_game_invitation",
                {
                    "protocol": "league.v2",
                    "message_type": "GAME_INVITATION",
                    "sender": f"referee:{config.referee_id}",
                    "timestamp": timestamp,
                    "conversation_id": conversation_id,
                    "league_id": league_id,
                    "round_id": round_id,
                    "match_id": match_id,
                    "game_type": "even_odd",
                    "opponent_id": player_b_id,
                    "role_in_match": "PLAYER_A"
                }
            )

            resp_b = await client.call_tool(
                player_b["endpoint"],
                "handle_game_invitation",
                {
                    "protocol": "league.v2",
                    "message_type": "GAME_INVITATION",
                    "sender": f"referee:{config.referee_id}",
                    "timestamp": timestamp,
                    "conversation_id": conversation_id,
                    "league_id": league_id,
                    "round_id": round_id,
                    "match_id": match_id,
                    "game_type": "even_odd",
                    "opponent_id": player_a_id,
                    "role_in_match": "PLAYER_B"
                }
            )

            # Verify both accepted
            result_a = resp_a.get("result", {})
            result_b = resp_b.get("result", {})

            # Player returns {"accept": True} in the result
            if not result_a.get("accept") or not result_b.get("accept"):
                logger.warning(
                    "Invitation rejected",
                    player_a_accept=result_a.get("accept"),
                    player_b_accept=result_b.get("accept")
                )
                return False

            logger.info("Both players accepted invitation", match_id=match_id)
            return True

        finally:
            await client.close()

    async def _request_move(self, match_id: str, player_id: str, opponent_id: str) -> Optional[str]:
        """Request parity choice from player."""
        client = MCPClient(timeout=self.choice_timeout)
        try:
            player = self.agent_registry.get_player(player_id)
            if not player:
                return None

            # Generate conversation_id and timestamp for this move request
            from datetime import datetime, timezone
            timestamp = datetime.now(timezone.utc).isoformat()
            conversation_id = f"conv_{match_id.lower().replace('_', '')}"

            response = await client.call_tool(
                player["endpoint"],
                "choose_parity",
                {
                    "protocol": "league.v2",
                    "message_type": "CHOOSE_PARITY_CALL",
                    "sender": f"referee:{config.referee_id}",
                    "timestamp": timestamp,
                    "conversation_id": conversation_id,
                    "match_id": match_id,
                    "player_id": player_id,
                    "game_type": "even_odd",
                    "context": {
                        "opponent_id": opponent_id,
                        "your_standings": {},
                        "opponent_standings": {}
                    },
                    "deadline": timestamp  # TODO: Calculate proper deadline
                }
            )

            result = response.get("result", {})
            # Player returns "parity_choice", not "choice"
            choice = result.get("parity_choice")

            if choice not in ["even", "odd"]:
                logger.error("Invalid choice", player_id=player_id, choice=choice)
                return None

            logger.info("Move received", player_id=player_id, choice=choice, match_id=match_id)
            return choice

        except Exception as e:
            logger.error("Move request failed", player_id=player_id, error=str(e))
            return None
        finally:
            await client.close()
