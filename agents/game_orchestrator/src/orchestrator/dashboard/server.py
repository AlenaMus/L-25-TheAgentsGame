"""
Dashboard Server - Real-time monitoring web interface.

Provides WebSocket-based real-time updates and REST API for tournament.
"""

import asyncio
import json
from typing import Dict, Set, Optional
from pathlib import Path
import websockets
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from .api_routes import APIRoutes
from .fallback_html import get_fallback_html


class DashboardServer:
    """Real-time dashboard with WebSocket updates and REST API."""

    def __init__(
        self,
        port: int = 9000,
        tournament_controller: Optional[object] = None
    ):
        """
        Initialize dashboard server.

        Args:
            port: Dashboard server port
            tournament_controller: TournamentController instance for API
        """
        self.port = port
        self.tournament = tournament_controller
        self.app = FastAPI(title="Game Orchestrator Dashboard")
        self.websocket_clients: Set[WebSocket] = set()
        self.current_state: Dict = {}

        self._setup_cors()
        self._setup_routes()
        if tournament_controller:
            self._setup_api_routes()

    def _setup_cors(self) -> None:
        """Setup CORS middleware for API access."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_api_routes(self) -> None:
        """Setup REST API routes."""
        api = APIRoutes(self.tournament)
        self.app.include_router(api.get_router())

    def _setup_routes(self) -> None:
        """Setup HTTP and WebSocket routes."""

        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_page():
            """Serve dashboard HTML."""
            # Try to serve enhanced frontend first
            frontend_path = (
                Path(__file__).parent.parent.parent.parent.parent /
                "frontend" / "index.html"
            )
            if frontend_path.exists():
                return frontend_path.read_text()

            # Fallback to embedded HTML
            html_path = Path(__file__).parent / "static" / "dashboard.html"
            if html_path.exists():
                return html_path.read_text()

            return get_fallback_html()

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_clients.add(websocket)
            logger.info("Dashboard client connected")

            try:
                # Send initial state
                await websocket.send_json(self.current_state)

                # Keep connection open
                while True:
                    await websocket.receive_text()

            except Exception as e:
                logger.debug("WebSocket disconnected", error=str(e))

            finally:
                self.websocket_clients.discard(websocket)

    async def start(self) -> None:
        """Start dashboard server."""
        import uvicorn

        logger.info(f"Starting dashboard on port {self.port}")

        config = uvicorn.Config(
            self.app, host="0.0.0.0", port=self.port, log_level="error"
        )
        server = uvicorn.Server(config)
        await server.serve()

    async def broadcast_update(self, update_type: str, data: Dict) -> None:
        """
        Broadcast update to all connected clients.

        Args:
            update_type: Type of update (health, standings, match, etc.)
            data: Update data
        """
        update = {
            "type": update_type,
            "data": data
        }

        self.current_state[update_type] = data

        # Broadcast to all clients
        disconnected = set()
        for client in self.websocket_clients:
            try:
                await client.send_json(update)
            except Exception:
                disconnected.add(client)

        # Remove disconnected clients
        self.websocket_clients -= disconnected

    async def get_current_state(self) -> Dict:
        """
        Get current dashboard state.

        Returns:
            Dictionary with current state
        """
        return self.current_state.copy()
