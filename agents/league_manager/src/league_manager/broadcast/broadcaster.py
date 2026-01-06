"""
HTTP broadcaster for sending messages to agents.

Handles concurrent HTTP requests with timeout and retry logic.
"""

import asyncio
from typing import List, Dict

from league_manager.broadcast.delivery_report import DeliveryReport
from league_manager.broadcast.message_sender import MessageSender
from league_manager.broadcast.result_processor import ResultProcessor
from league_manager.utils.logger import logger


class Broadcaster:
    """
    HTTP client for broadcasting messages to multiple agents.

    Sends messages concurrently with timeout and retry logic.

    Example:
        >>> broadcaster = Broadcaster(timeout=5.0, max_retries=2)
        >>> report = await broadcaster.broadcast_to_players(
        ...     players=[{"player_id": "P01", "endpoint": "http://..."}],
        ...     message={"message_type": "ROUND_ANNOUNCEMENT", ...}
        ... )
        >>> print(f"Delivered to {report.successful}/{report.total}")
    """

    def __init__(self, timeout: float = 5.0, max_retries: int = 2):
        """
        Initialize broadcaster.

        Args:
            timeout: Timeout in seconds per request
            max_retries: Maximum retry attempts for failed requests
        """
        self.sender = MessageSender(timeout, max_retries)

    async def broadcast_to_players(
        self,
        players: List[Dict],
        message: Dict
    ) -> DeliveryReport:
        """Broadcast message to all registered players."""
        return await self._broadcast_to_agents(
            agents=players,
            agent_type="player",
            message=message
        )

    async def broadcast_to_referees(
        self,
        referees: List[Dict],
        message: Dict
    ) -> DeliveryReport:
        """Broadcast message to all registered referees."""
        return await self._broadcast_to_agents(
            agents=referees,
            agent_type="referee",
            message=message
        )

    async def broadcast_to_all(
        self,
        players: List[Dict],
        referees: List[Dict],
        message: Dict
    ) -> DeliveryReport:
        """Broadcast message to both players and referees."""
        all_agents = [
            {**p, "_agent_type": "player"} for p in players
        ] + [
            {**r, "_agent_type": "referee"} for r in referees
        ]
        return await self._broadcast_to_agents(
            agents=all_agents,
            agent_type="mixed",
            message=message
        )

    async def _broadcast_to_agents(
        self,
        agents: List[Dict],
        agent_type: str,
        message: Dict
    ) -> DeliveryReport:
        """
        Internal broadcast implementation.

        Sends messages concurrently using asyncio.gather.

        Args:
            agents: List of agent metadata dictionaries
            agent_type: Type of agents (for logging)
            message: Message to broadcast

        Returns:
            DeliveryReport with delivery statistics
        """
        report = DeliveryReport()
        report.total = len(agents)

        if not agents:
            logger.warning("No agents to broadcast to", agent_type=agent_type)
            return report

        # Send to all agents concurrently
        tasks = [
            self.sender.send_to_agent(agent, message)
            for agent in agents
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        ResultProcessor.process_results(agents, results, report)

        logger.info(
            "Broadcast complete",
            agent_type=agent_type,
            successful=report.successful,
            failed=report.failed,
            total=report.total
        )
        return report


__all__ = ["Broadcaster", "DeliveryReport"]
