"""
Configuration management for Player Agent P01.

Loads configuration from environment variables and config files.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Config(BaseSettings):
    """
    Configuration for Player Agent P01.

    Attributes:
        agent_id: Agent identifier (e.g., "P01")
        port: HTTP server port
        league_manager_url: League Manager endpoint
        auth_token: Authentication token (set after registration)
        league_id: League identifier (set after registration)

    Example:
        >>> config = Config()
        >>> print(config.port)
        8101
    """

    # Agent identification
    agent_id: Optional[str] = None
    temp_name: str = "player_p01"
    display_name: str = "Agent P01"

    # Network configuration
    port: int = 8101
    league_manager_url: str = "http://localhost:8000/mcp"

    # Credentials (set after registration)
    auth_token: Optional[str] = None
    league_id: Optional[str] = None

    class Config:
        env_file = ".env"
        # Don't use prefix to support both AGENT_ID and PLAYER_AGENT_ID
        env_prefix = ""

    def __init__(self, **kwargs):
        """Initialize config, preferring non-prefixed env vars."""
        super().__init__(**kwargs)
        # Fallback to default agent_id if not set
        if not self.agent_id:
            self.agent_id = os.getenv("AGENT_ID") or os.getenv("PLAYER_AGENT_ID") or "P01"
        # Also check for PORT env var
        port_env = os.getenv("PORT")
        if port_env:
            self.port = int(port_env)

    def set_credentials(
        self,
        agent_id: str,
        auth_token: str,
        league_id: str
    ):
        """
        Store credentials received during registration.

        Args:
            agent_id: Assigned agent ID
            auth_token: Authentication token
            league_id: League identifier
        """
        self.agent_id = agent_id
        self.auth_token = auth_token
        self.league_id = league_id


# Global configuration instance
config = Config()
