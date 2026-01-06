"""
Configuration for League Manager.

Loads settings from environment variables and provides defaults.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Config(BaseSettings):
    """League Manager configuration."""

    # Server settings
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # League settings
    league_id: str = Field(default="league_2025_even_odd", description="League ID")
    max_players: int = Field(default=50, description="Maximum players")
    max_referees: int = Field(default=10, description="Maximum referees")
    
    # Data paths
    data_dir: str = Field(default="SHARED/data", description="Data directory")
    log_dir: str = Field(default="SHARED/logs", description="Log directory")
    config_dir: str = Field(default="SHARED/config", description="Config directory")
    
    # Protocol
    protocol_version: str = Field(default="league.v2", description="Protocol version")
    
    # Environment
    env: str = Field(default="development", description="Environment")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton instance
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get configuration instance.
    
    Returns:
        Config: Configuration singleton
        
    Example:
        >>> config = get_config()
        >>> print(config.league_id)
        'league_2025_even_odd'
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
