"""
Error Recovery Manager - Handle failures and implement recovery strategies.

Provides pluggable error handlers with exponential backoff retries.
"""

import asyncio
from typing import Dict, Callable
from loguru import logger


class ErrorRecoveryManager:
    """Manages error recovery with pluggable handlers."""

    def __init__(self):
        """Initialize error recovery manager."""
        self.handlers: Dict[str, Callable] = {}
        self.failure_history: Dict[str, list] = {}

    def register_handler(self, error_type: str, handler: Callable) -> None:
        """
        Register error handler for specific error type.

        Args:
            error_type: Type of error (e.g., "AGENT_CRASH", "TIMEOUT")
            handler: Async function to handle the error
        """
        self.handlers[error_type] = handler
        logger.debug(f"Registered handler for {error_type}")

    async def handle_error(self, error_type: str, context: Dict) -> bool:
        """
        Handle error using registered handler.

        Args:
            error_type: Type of error
            context: Error context dictionary

        Returns:
            True if error handled successfully
        """
        logger.warning(f"Handling error: {error_type}", context=context)

        # Track failure
        if error_type not in self.failure_history:
            self.failure_history[error_type] = []
        self.failure_history[error_type].append(context)

        # Get handler
        handler = self.handlers.get(error_type)
        if not handler:
            logger.error(f"No handler registered for {error_type}")
            return False

        try:
            result = await handler(context)
            logger.info(f"Error handled: {error_type}", success=result)
            return result

        except Exception as e:
            logger.error(
                f"Handler failed for {error_type}", error=str(e)
            )
            return False

    async def restart_agent(
        self, agent_id: str, restart_fn: Callable, max_retries: int = 3
    ) -> bool:
        """
        Restart agent with exponential backoff.

        Args:
            agent_id: Agent identifier
            restart_fn: Async function to restart the agent
            max_retries: Maximum retry attempts

        Returns:
            True if restart successful
        """
        logger.info(f"Restarting agent {agent_id}", max_retries=max_retries)

        for attempt in range(max_retries):
            delay = 2 ** attempt  # Exponential backoff
            logger.debug(
                f"Restart attempt {attempt + 1}/{max_retries}",
                agent_id=agent_id,
                delay=delay
            )

            if attempt > 0:
                await asyncio.sleep(delay)

            try:
                success = await restart_fn(agent_id)
                if success:
                    logger.info(f"Agent {agent_id} restarted successfully")
                    return True

            except Exception as e:
                logger.error(
                    f"Restart attempt failed", agent_id=agent_id, error=str(e)
                )

        logger.error(f"All restart attempts failed for {agent_id}")
        return False

    def get_failure_count(self, error_type: str) -> int:
        """
        Get count of failures for error type.

        Args:
            error_type: Type of error

        Returns:
            Number of times this error occurred
        """
        return len(self.failure_history.get(error_type, []))

    def clear_history(self, error_type: str = None) -> None:
        """
        Clear failure history.

        Args:
            error_type: Specific error type to clear, or None for all
        """
        if error_type:
            self.failure_history.pop(error_type, None)
            logger.debug(f"Cleared history for {error_type}")
        else:
            self.failure_history.clear()
            logger.debug("Cleared all failure history")
