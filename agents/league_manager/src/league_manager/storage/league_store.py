"""
League data persistence.

Stores and retrieves league data (players, schedule, standings) from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..utils.logger import logger


class LeagueStore:
    """Manages league data persistence."""
    
    def __init__(self, data_dir: str = "SHARED/data", league_id: str = "league_2025_even_odd"):
        """
        Initialize league store.
        
        Args:
            data_dir: Base data directory
            league_id: League identifier
        """
        self.league_id = league_id
        self.base_dir = Path(data_dir) / "leagues" / league_id
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
    def save_schedule(self, schedule: List[List[Dict]]) -> None:
        """
        Save tournament schedule.
        
        Args:
            schedule: List of rounds, each containing matches
            
        Example:
            >>> store.save_schedule(schedule)
        """
        file_path = self.base_dir / "schedule.json"
        with open(file_path, 'w') as f:
            json.dump(schedule, f, indent=2)
        logger.info("Schedule saved", path=str(file_path))
        
    def load_schedule(self) -> Optional[List[List[Dict]]]:
        """
        Load tournament schedule.
        
        Returns:
            Schedule or None if not found
        """
        file_path = self.base_dir / "schedule.json"
        if not file_path.exists():
            return None
        with open(file_path, 'r') as f:
            return json.load(f)
            
    def save_standings(self, standings: List[Dict]) -> None:
        """
        Save current standings.
        
        Args:
            standings: List of player standings
        """
        file_path = self.base_dir / "standings.json"
        with open(file_path, 'w') as f:
            json.dump(standings, f, indent=2)
        logger.info("Standings saved", path=str(file_path))
        
    def load_standings(self) -> List[Dict]:
        """
        Load current standings.

        Returns:
            List of player standings
        """
        file_path = self.base_dir / "standings.json"
        if not file_path.exists():
            return []
        with open(file_path, 'r') as f:
            return json.load(f)

    def update_match_status(self, round_idx: int, match_idx: int, status: str) -> None:
        """
        Update match status in schedule.

        Args:
            round_idx: Round index (0-based)
            match_idx: Match index within round (0-based)
            status: New status (PENDING, IN_PROGRESS, COMPLETED)
        """
        schedule = self.load_schedule()
        if schedule and round_idx < len(schedule) and match_idx < len(schedule[round_idx]):
            schedule[round_idx][match_idx]["status"] = status
            self.save_schedule(schedule)
            logger.debug(f"Match status updated to {status}", round=round_idx+1, match=match_idx+1)
