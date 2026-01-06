"""
Structured JSON logging for League Manager.

Provides configured logger instance for all modules.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger


def setup_logger(agent_id: str = "league_manager", log_dir: str = "SHARED/logs/league") -> None:
    """
    Configure structured JSON logging.
    
    Args:
        agent_id: Agent identifier
        log_dir: Directory for log files
        
    Example:
        >>> setup_logger("league_manager")
        >>> logger.info("League started")
    """
    # Remove default handler
    logger.remove()
    
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{agent_id}.log.jsonl"
    
    # Console handler (human-readable)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> | <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )
    
    # File handler (JSON Lines)
    logger.add(
        str(log_file),
        format="{message}",
        serialize=True,
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="gz"
    )
    
    # Add agent_id to all logs
    logger.configure(extra={"agent_id": agent_id})


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
        "agent_id": record["extra"].get("agent_id", "league_manager"),
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


__all__ = ["logger", "setup_logger"]
