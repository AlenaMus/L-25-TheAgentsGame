"""
Helper utility functions for referee agent.

Provides common functionality used across multiple modules.
"""

from datetime import datetime, timezone


def get_utc_timestamp() -> str:
    """
    Get current UTC timestamp in ISO format.

    Returns:
        str: Timestamp in format "YYYY-MM-DDTHH:MM:SSZ"

    Example:
        >>> ts = get_utc_timestamp()
        >>> print(ts)
        "2025-12-24T10:15:30Z"
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
