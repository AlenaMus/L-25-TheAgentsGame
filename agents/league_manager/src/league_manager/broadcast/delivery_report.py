"""
Delivery report for broadcast operations.

Tracks success/failure statistics for message broadcasts.
"""

from typing import List, Dict


class DeliveryReport:
    """
    Report of broadcast delivery status.

    Attributes:
        total: Total number of agents
        successful: Number of successful deliveries
        failed: Number of failed deliveries
        failed_agents: List of agent IDs that failed
        errors: Dictionary mapping agent_id to error message
    """

    def __init__(self):
        """Initialize empty delivery report."""
        self.total: int = 0
        self.successful: int = 0
        self.failed: int = 0
        self.failed_agents: List[str] = []
        self.errors: Dict[str, str] = {}

    def to_dict(self) -> Dict:
        """
        Convert report to dictionary.

        Returns:
            Dictionary with delivery statistics
        """
        success_rate = (
            f"{(self.successful/self.total*100):.1f}%"
            if self.total > 0
            else "0%"
        )
        return {
            "total": self.total,
            "successful": self.successful,
            "failed": self.failed,
            "failed_agents": self.failed_agents,
            "success_rate": success_rate
        }
