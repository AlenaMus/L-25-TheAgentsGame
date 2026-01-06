"""
API Routes - REST API endpoints for tournament data access.

Provides REST endpoints for tournament information, standings, and matches.
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from loguru import logger


class TournamentInfo(BaseModel):
    """Tournament information response model."""
    league_id: str
    current_round: int
    total_rounds: int
    total_players: int
    status: str


class PlayerStats(BaseModel):
    """Player statistics response model."""
    player_id: str
    display_name: Optional[str]
    points: int
    wins: int
    losses: int
    ties: int
    win_rate: float


class MatchResult(BaseModel):
    """Match result response model."""
    match_id: str
    round_number: int
    player1_id: str
    player2_id: str
    winner_id: Optional[str]
    drawn_number: Optional[int]
    status: str


class APIRoutes:
    """REST API routes for tournament data."""

    def __init__(self, tournament_controller):
        """
        Initialize API routes.

        Args:
            tournament_controller: TournamentController instance
        """
        self.tournament = tournament_controller
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup all API routes."""

        @self.router.get("/api/tournament", response_model=TournamentInfo)
        async def get_tournament_info():
            """Get current tournament information."""
            try:
                state = self.tournament.get_current_state()
                round_status = await self.tournament.client.get_round_status()
                regs = await self.tournament.client.get_registrations()

                return TournamentInfo(
                    league_id="LEAGUE_001",
                    current_round=state.current_round,
                    total_rounds=state.total_rounds,
                    total_players=len(regs.get("players", [])),
                    status=state.stage.value
                )
            except Exception as e:
                logger.error("Failed to get tournament info", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/api/standings", response_model=List[PlayerStats])
        async def get_standings():
            """Get current tournament standings."""
            try:
                standings = await self.tournament.client.get_standings()

                return [
                    PlayerStats(
                        player_id=entry.get("player_id", ""),
                        display_name=entry.get("display_name"),
                        points=entry.get("points", 0),
                        wins=entry.get("wins", 0),
                        losses=entry.get("losses", 0),
                        ties=entry.get("ties", 0),
                        win_rate=entry.get("win_rate", 0.0)
                    )
                    for entry in standings
                ]
            except Exception as e:
                logger.error("Failed to get standings", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/api/matches", response_model=List[MatchResult])
        async def get_matches(limit: int = 10, round_id: Optional[int] = None):
            """
            Get match results.

            Args:
                limit: Maximum number of matches to return
                round_id: Filter by round (None for all rounds)
            """
            try:
                matches = await self.tournament.client.get_matches(round_id)

                # Convert to response model and limit
                results = [
                    MatchResult(
                        match_id=match.get("match_id", ""),
                        round_number=match.get("round_number", 0),
                        player1_id=match.get("player1_id", ""),
                        player2_id=match.get("player2_id", ""),
                        winner_id=match.get("winner_id"),
                        drawn_number=match.get("drawn_number"),
                        status=match.get("status", "completed")
                    )
                    for match in matches[:limit]
                ]

                return results
            except Exception as e:
                logger.error("Failed to get matches", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

        @self.router.get("/api/players", response_model=List[Dict])
        async def get_players():
            """Get list of registered players."""
            try:
                regs = await self.tournament.client.get_registrations()
                return regs.get("players", [])
            except Exception as e:
                logger.error("Failed to get players", error=str(e))
                raise HTTPException(status_code=500, detail=str(e))

    def get_router(self) -> APIRouter:
        """Get configured router."""
        return self.router
