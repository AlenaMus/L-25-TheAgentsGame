"""
Structured JSON logging for Player Agent P01.

Provides configured logger instance for all modules.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger as _logger

# Remove default handler
_logger.remove()


def setup_logger(agent_id: str, log_dir: str = "SHARED/logs/agents") -> None:
    """
    Configure structured JSON logging.

    Args:
        agent_id: Agent identifier (e.g., "P01")
        log_dir: Directory for log files

    Example:
        >>> setup_logger("P01")
        >>> logger.info("Agent started")
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{agent_id}.log.jsonl"

    # Console handler (development)
    _logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )

    # File handler (production - JSON Lines)
    _logger.add(
        str(log_file),
        serialize=True,
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="gz"
    )

    # Add agent_id to all logs
    _logger.configure(extra={"agent_id": agent_id})


def _json_formatter(record: dict) -> str:
    """
    Format log record as JSON.

    Args:
        record: Log record dictionary

    Returns:
        str: JSON formatted log entry
    """
    log_entry = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "agent_id": record["extra"].get("agent_id", "UNKNOWN"),
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }

    # Add extra fields
    for key, value in record["extra"].items():
        if key != "agent_id":
            log_entry[key] = value

    return json.dumps(log_entry)


# Export logger
logger = _logger
__all__ = ["logger", "setup_logger"]
