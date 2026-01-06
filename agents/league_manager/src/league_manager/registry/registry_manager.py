"""
Agent registry manager.

High-level registry operations coordinating token generation and storage.
"""

from typing import Tuple
from league_manager.registry.agent_store import AgentStore
from league_manager.registry.token_generator import generate_auth_token
from league_manager.utils.logger import logger


class RegistryManager:
    """
    Manages agent registration with ID assignment and token generation.

    Attributes:
        agent_store: Storage for agents and tokens
        max_players: Maximum allowed players
        max_referees: Maximum allowed referees
    """

    def __init__(
        self,
        agent_store: AgentStore = None,
        max_players: int = 100,
        max_referees: int = 10
    ):
        """Initialize registry manager."""
        self.agent_store = agent_store or AgentStore()
        self.max_players = max_players
        self.max_referees = max_referees

    def register_player(
        self,
        display_name: str,
        endpoint: str,
        game_types: list = None,
        version: str = "1.0.0"
    ) -> Tuple[str, str]:
        """
        Register a new player.

        Args:
            display_name: Human-readable name
            endpoint: MCP endpoint URL
            game_types: List of supported game types
            version: Agent version

        Returns:
            Tuple of (player_id, auth_token)

        Raises:
            ValueError: If league is full
        """
        # Check capacity
        if self.agent_store.get_player_count() >= self.max_players:
            raise ValueError(f"League full: maximum {self.max_players} players allowed")

        # Generate ID and token
        player_id = self._generate_player_id()
        auth_token = generate_auth_token("player", player_id)

        # Store player
        self.agent_store.add_player(
            player_id=player_id,
            display_name=display_name,
            endpoint=endpoint,
            auth_token=auth_token,
            game_types=game_types,
            version=version
        )

        logger.info("Player registered", player_id=player_id, display_name=display_name)
        return player_id, auth_token

    def register_referee(
        self,
        display_name: str,
        endpoint: str,
        max_concurrent_matches: int = 2,
        game_types: list = None,
        version: str = "1.0.0"
    ) -> Tuple[str, str]:
        """
        Register a new referee.

        Args:
            display_name: Human-readable name
            endpoint: MCP endpoint URL
            max_concurrent_matches: Maximum concurrent matches
            game_types: List of supported game types
            version: Agent version

        Returns:
            Tuple of (referee_id, auth_token)

        Raises:
            ValueError: If maximum referees reached
        """
        # Check capacity
        if self.agent_store.get_referee_count() >= self.max_referees:
            raise ValueError(f"Maximum {self.max_referees} referees allowed")

        # Generate ID and token
        referee_id = self._generate_referee_id()
        auth_token = generate_auth_token("referee", referee_id)

        # Store referee
        self.agent_store.add_referee(
            referee_id=referee_id,
            display_name=display_name,
            endpoint=endpoint,
            auth_token=auth_token,
            max_concurrent_matches=max_concurrent_matches,
            game_types=game_types,
            version=version
        )

        logger.info("Referee registered", referee_id=referee_id, display_name=display_name)
        return referee_id, auth_token

    def _generate_player_id(self) -> str:
        """Generate sequential player ID (P01, P02, ...)."""
        count = self.agent_store.get_player_count()
        return f"P{count + 1:02d}"

    def _generate_referee_id(self) -> str:
        """Generate sequential referee ID (REF01, REF02, ...)."""
        count = self.agent_store.get_referee_count()
        return f"REF{count + 1:02d}"


__all__ = ["RegistryManager"]
