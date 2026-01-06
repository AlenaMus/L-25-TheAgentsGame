"""
Configuration management for Game Orchestrator.

Loads agent configurations and orchestrator settings from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    """Configuration for a single agent."""

    agent_id: str
    agent_type: str
    port: int
    working_dir: str
    startup_command: List[str]
    health_endpoint: str
    dependencies: List[str] = Field(default_factory=list)


class OrchestratorConfig(BaseModel):
    """Orchestrator settings."""

    dashboard_port: int = 9000
    health_check_interval: int = 5
    startup_grace_period: int = 2
    agent_startup_timeout: int = 30
    auto_start: bool = True
    registration_timeout: int = 120
    min_players: int = 2
    min_referees: int = 1


class Config:
    """Main configuration loader."""

    def __init__(self, config_path: str):
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to agents.json configuration file
        """
        self.config_path = Path(config_path)
        with open(self.config_path) as f:
            data = json.load(f)

        self.agents: Dict[str, AgentConfig] = {
            agent["agent_id"]: AgentConfig(**agent)
            for agent in data["agents"]
        }
        self.orchestrator = OrchestratorConfig(**data.get("orchestrator", {}))

    def get_agent(self, agent_id: str) -> AgentConfig:
        """
        Get configuration for specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            AgentConfig for the agent

        Raises:
            KeyError: If agent_id not found
        """
        return self.agents[agent_id]

    def get_agents_by_type(self, agent_type: str) -> List[AgentConfig]:
        """
        Get all agents of a specific type.

        Args:
            agent_type: Type of agent (LEAGUE_MANAGER, REFEREE, PLAYER)

        Returns:
            List of matching AgentConfig objects
        """
        return [
            agent for agent in self.agents.values()
            if agent.agent_type == agent_type
        ]
