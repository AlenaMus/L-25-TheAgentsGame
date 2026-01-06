"""
Result processing for broadcast operations.

Processes broadcast results and updates delivery reports.
"""

from typing import List, Dict, Any

from league_manager.broadcast.delivery_report import DeliveryReport
from league_manager.utils.logger import logger


class ResultProcessor:
    """Processes broadcast results and updates delivery reports."""

    @staticmethod
    def process_results(
        agents: List[Dict],
        results: List[Any],
        report: DeliveryReport
    ) -> None:
        """
        Process broadcast results and update delivery report.

        Args:
            agents: List of agent metadata dictionaries
            results: List of results from asyncio.gather
            report: DeliveryReport to update
        """
        for agent, result in zip(agents, results):
            agent_id = ResultProcessor._get_agent_id(agent)

            if isinstance(result, Exception):
                report.failed += 1
                report.failed_agents.append(agent_id)
                report.errors[agent_id] = str(result)
                logger.error(
                    "Broadcast failed",
                    agent_id=agent_id,
                    error=str(result)
                )
            elif result is True:
                report.successful += 1
            else:
                report.failed += 1
                report.failed_agents.append(agent_id)
                report.errors[agent_id] = "Unknown error"

    @staticmethod
    def _get_agent_id(agent: Dict) -> str:
        """
        Extract agent ID from metadata.

        Args:
            agent: Agent metadata dictionary

        Returns:
            Agent ID string
        """
        return (
            agent.get("player_id") or
            agent.get("referee_id") or
            "unknown"
        )
