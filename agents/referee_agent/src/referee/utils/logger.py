"""
Structured JSON logging for referee agent.

Provides configured logger instance for all modules.
Logs to both console (development) and file (production).
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger as _logger


def setup_logger(agent_id: str, log_dir: str = "SHARED/logs/agents") -> None:
    """
    Configure structured JSON logging for referee.

    Args:
        agent_id: Referee identifier (e.g., "REF01")
        log_dir: Directory for log files

    Example:
        >>> setup_logger("REF01")
        >>> logger.info("Referee started", version="1.0.0")
    """
    # Remove default handler
    _logger.remove()

    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{agent_id}.log.jsonl"

    # Console handler (development)
    _logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> | "
               "<level>{message}</level>",
        level="DEBUG",
        colorize=True
    )

    # File handler (JSON Lines, production)
    _logger.add(
        str(log_file),
        serialize=True,  # Use built-in JSON serialization instead of custom formatter
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
        record: Loguru record dictionary

    Returns:
        JSON string with standard fields
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
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


# Export configured logger
logger = _logger
