"""
Mock Referee for integration testing.

Simulates referee behavior for testing player agent.
"""

from typing import Dict, Any, Optional, List
from .base_referee import BaseReferee


class MockReferee(BaseReferee):
    """
    Mock Referee that simulates referee behavior.

    Sends JSON-RPC requests to player agent and validates responses.

    Example:
        >>> referee = MockReferee("http://localhost:8101/mcp")
        >>> response = await referee.send_invitation("R1M1", "P01", "P02")
        >>> assert response["status"] == "accepted"
    """

    async def send_invitation(
        self,
        match_id: str,
        player_id: str,
        opponent_id: str,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """
        Send game invitation to player.

        Args:
            match_id: Match identifier
            player_id: Player identifier
            opponent_id: Opponent identifier
            timeout: Timeout for response

        Returns:
            dict: GAME_JOIN_ACK response
        """
        params = {
            "protocol": "league.v2",
            "message_type": "GAME_INVITATION",
            "sender": f"referee:{self.referee_id}",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"conv{match_id}",
            "match_id": match_id,
            "game_type": "even_odd",
            "player_id": player_id,
            "opponent_id": opponent_id,
            "role": "PLAYER_A"
        }

        return await self.send_jsonrpc_request(
            "handle_game_invitation",
            params,
            timeout
        )

    async def request_move(
        self,
        match_id: str,
        player_id: str,
        opponent_id: str,
        standings: Optional[List[Dict]] = None,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """
        Request parity choice from player.

        Args:
            match_id: Match identifier
            player_id: Player identifier
            opponent_id: Opponent identifier
            standings: Current league standings
            timeout: Timeout for response

        Returns:
            dict: CHOOSE_PARITY_RESPONSE
        """
        params = {
            "protocol": "league.v2",
            "message_type": "CHOOSE_PARITY_CALL",
            "sender": f"referee:{self.referee_id}",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"conv{match_id}",
            "match_id": match_id,
            "game_type": "even_odd",
            "player_id": player_id,
            "context": {
                "opponent_id": opponent_id,
                "your_standings": standings or {}
            },
            "deadline": self._get_timestamp()
        }

        return await self.send_jsonrpc_request(
            "choose_parity",
            params,
            timeout
        )

    async def send_result(
        self,
        match_id: str,
        player_id: str,
        winner_id: Optional[str],
        drawn_number: int,
        choices: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Send match result notification to player.

        Args:
            match_id: Match identifier
            player_id: Player identifier
            winner_id: Winner player ID (None for tie)
            drawn_number: Drawn number (1-10)
            choices: Player choices dict

        Returns:
            dict: Acknowledgment response
        """
        status = "WIN" if winner_id else "TIE"
        number_parity = "even" if drawn_number % 2 == 0 else "odd"

        params = {
            "protocol": "league.v2",
            "message_type": "GAME_OVER",
            "sender": f"referee:{self.referee_id}",
            "timestamp": self._get_timestamp(),
            "conversation_id": f"conv{match_id}",
            "match_id": match_id,
            "player_id": player_id,
            "game_result": {
                "status": status,
                "winner_player_id": winner_id,
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "choices": choices
            }
        }

        return await self.send_jsonrpc_request(
            "notify_match_result",
            params,
            timeout=10.0
        )
