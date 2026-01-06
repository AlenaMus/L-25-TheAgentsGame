"""
Low-level HTTP message sending with retry logic.

Handles individual agent message delivery with timeouts and retries.
"""

import asyncio
from typing import Dict
import httpx
from league_manager.utils.logger import logger


class MessageSender:
    """
    HTTP client for sending messages to individual agents.

    Handles retry logic and error handling for single agent delivery.
    """

    def __init__(self, timeout: float = 5.0, max_retries: int = 2):
        """
        Initialize message sender.

        Args:
            timeout: Timeout in seconds per request
            max_retries: Maximum retry attempts for failed requests
        """
        self.timeout = timeout
        self.max_retries = max_retries

    async def send_to_agent(self, agent: Dict, message: Dict) -> bool:
        """
        Send message to single agent with retry logic.

        Args:
            agent: Agent metadata dictionary
            message: Message to send

        Returns:
            True if successful, False otherwise

        Raises:
            Exception: If all retries fail
        """
        agent_id = self._get_agent_id(agent)
        endpoint = agent.get("endpoint")

        if not endpoint:
            logger.error("Agent missing endpoint", agent_id=agent_id)
            raise ValueError(f"Agent {agent_id} has no endpoint")

        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(endpoint, json=message)
                    response.raise_for_status()
                    logger.debug(
                        "Message delivered",
                        agent_id=agent_id,
                        attempt=attempt + 1
                    )
                    return True

            except httpx.TimeoutException:
                logger.warning(
                    "Timeout sending to agent",
                    agent_id=agent_id,
                    attempt=attempt + 1,
                    max_retries=self.max_retries
                )
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

            except httpx.HTTPStatusError as e:
                logger.warning(
                    "HTTP error from agent",
                    agent_id=agent_id,
                    status=e.response.status_code,
                    attempt=attempt + 1
                )
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

            except Exception as e:
                logger.error(
                    "Unexpected error sending to agent",
                    agent_id=agent_id,
                    error=str(e),
                    attempt=attempt + 1
                )
                if attempt == self.max_retries:
                    raise
                await asyncio.sleep(0.5 * (attempt + 1))

        return False

    def _get_agent_id(self, agent: Dict) -> str:
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
