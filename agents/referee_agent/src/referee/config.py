"""
Configuration management for referee agent.

Loads configuration from environment variables and provides
typed access to all settings.
"""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Config(BaseSettings):
    """
    Referee configuration loaded from environment variables.

    Attributes:
        referee_id: Unique referee identifier (e.g., "REF01")
        referee_port: HTTP port for MCP server
        referee_display_name: Human-readable name
        league_manager_endpoint: URL of league manager
        max_concurrent_matches: Maximum simultaneous games
        invitation_timeout: Timeout for game invitations (seconds)
        choice_timeout: Timeout for parity choices (seconds)
        auth_token: Authentication token (set after registration)
        league_id: League identifier (set after registration)
    """

    referee_id: str = "REF01"
    referee_port: int = 8001
    referee_display_name: str = "Referee Alpha"
    league_manager_endpoint: str = "http://localhost:8000/mcp"
    max_concurrent_matches: int = 2
    invitation_timeout: int = 5
    choice_timeout: int = 30

    # Set after registration
    auth_token: Optional[str] = None
    league_id: Optional[str] = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def __init__(self, **kwargs):
        """Initialize config, reading from AGENT_ID and PORT env vars."""
        super().__init__(**kwargs)
        # Support AGENT_ID environment variable for referee_id
        agent_id_env = os.getenv("AGENT_ID")
        if agent_id_env:
            self.referee_id = agent_id_env
        # Support PORT environment variable for referee_port
        port_env = os.getenv("PORT")
        if port_env:
            self.referee_port = int(port_env)

    def set_credentials(
        self,
        referee_id: str,
        auth_token: str,
        league_id: str
    ) -> None:
        """
        Set credentials after successful registration.

        Args:
            referee_id: Assigned referee ID
            auth_token: Authentication token
            league_id: League identifier
        """
        self.referee_id = referee_id
        self.auth_token = auth_token
        self.league_id = league_id


# Global configuration instance
config = Config()
