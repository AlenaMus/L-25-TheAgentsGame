"""
Log Aggregator - Collect and analyze logs from all agents.

Tails log files and provides error filtering and pattern analysis.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional, Callable
from loguru import logger


class LogAggregator:
    """Aggregates and analyzes logs from all agents."""

    def __init__(self, log_dir: str = "SHARED/logs/agents"):
        """
        Initialize log aggregator.

        Args:
            log_dir: Directory containing agent log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    async def tail_logs(
        self, agent_id: str, callback: Callable
    ) -> None:
        """
        Tail logs for a specific agent.

        Args:
            agent_id: Agent identifier
            callback: Async function called with each log entry
        """
        log_file = self.log_dir / f"{agent_id}.log.jsonl"

        if not log_file.exists():
            logger.warning(f"Log file not found for {agent_id}")
            return

        try:
            with open(log_file, 'r') as f:
                # Skip to end
                f.seek(0, 2)

                # Tail indefinitely
                while True:
                    line = f.readline()
                    if line:
                        try:
                            log_entry = json.loads(line)
                            await callback(log_entry)
                        except json.JSONDecodeError:
                            logger.warning("Invalid JSON in log file")

        except Exception as e:
            logger.error(f"Error tailing logs for {agent_id}", error=str(e))

    async def get_errors(
        self,
        since: Optional[str] = None,
        agent_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Get error log entries.

        Args:
            since: ISO timestamp to filter from (optional)
            agent_id: Specific agent ID to filter (optional)

        Returns:
            List of error log entries
        """
        errors = []

        # Determine which log files to read
        if agent_id:
            log_files = [self.log_dir / f"{agent_id}.log.jsonl"]
        else:
            log_files = list(self.log_dir.glob("*.log.jsonl"))

        for log_file in log_files:
            if not log_file.exists():
                continue

            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)

                            # Filter by level
                            if entry.get("level") not in ["ERROR", "CRITICAL"]:
                                continue

                            # Filter by timestamp
                            if since and entry.get("timestamp", "") < since:
                                continue

                            errors.append(entry)

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.error(f"Error reading {log_file}", error=str(e))

        return errors

    async def analyze_patterns(self) -> Dict:
        """
        Analyze log patterns for anomalies.

        Returns:
            Dictionary with pattern analysis results
        """
        analysis = {
            "total_errors": 0,
            "errors_by_agent": {},
            "errors_by_type": {},
            "common_errors": []
        }

        log_files = list(self.log_dir.glob("*.log.jsonl"))

        for log_file in log_files:
            agent_id = log_file.stem.replace(".log", "")

            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line)

                            if entry.get("level") in ["ERROR", "CRITICAL"]:
                                analysis["total_errors"] += 1

                                # Count by agent
                                if agent_id not in analysis["errors_by_agent"]:
                                    analysis["errors_by_agent"][agent_id] = 0
                                analysis["errors_by_agent"][agent_id] += 1

                                # Count by type
                                error_type = entry.get("error_type", "UNKNOWN")
                                if error_type not in analysis["errors_by_type"]:
                                    analysis["errors_by_type"][error_type] = 0
                                analysis["errors_by_type"][error_type] += 1

                        except json.JSONDecodeError:
                            continue

            except Exception as e:
                logger.error(f"Error analyzing {log_file}", error=str(e))

        # Find most common errors
        if analysis["errors_by_type"]:
            sorted_errors = sorted(
                analysis["errors_by_type"].items(),
                key=lambda x: x[1],
                reverse=True
            )
            analysis["common_errors"] = sorted_errors[:5]

        return analysis
