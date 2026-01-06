"""
Command-line interface for Game Orchestrator.

Provides the entry point for running the orchestrator from the command line.
"""

import asyncio
import sys
import argparse
from loguru import logger

from .main import GameOrchestrator


def configure_logging() -> None:
    """Configure loguru logging for orchestrator."""
    logger.remove()

    # Console logging
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # File logging (structured JSON)
    logger.add(
        "SHARED/logs/orchestrator/orchestrator.log.jsonl",
        format="{message}",
        serialize=True,
        level="DEBUG"
    )


async def run_orchestrator(config_path: str) -> int:
    """
    Create and run orchestrator.

    Args:
        config_path: Path to configuration file

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    configure_logging()

    orchestrator = GameOrchestrator(config_path)
    success = await orchestrator.run()

    return 0 if success else 1


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Game Orchestrator - Tournament System Controller"
    )
    parser.add_argument(
        "--config",
        default="config/agents.json",
        help="Path to agents configuration file"
    )
    args = parser.parse_args()

    # Run orchestrator
    exit_code = asyncio.run(run_orchestrator(args.config))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
