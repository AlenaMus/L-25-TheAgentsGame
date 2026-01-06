"""
Simple dashboard test - runs just the dashboard server.
"""
import asyncio
import sys
from pathlib import Path

# Add orchestrator to path
sys.path.insert(0, str(Path(__file__).parent / "agents" / "game_orchestrator" / "src"))

from orchestrator.dashboard.server import DashboardServer


async def main():
    """Run standalone dashboard for testing."""
    print("=" * 60)
    print("Starting Dashboard Server")
    print("=" * 60)
    print()
    print("Dashboard URL: http://localhost:9000")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 60)
    print()

    dashboard = DashboardServer(port=9000)

    # Broadcast initial test data
    await dashboard.broadcast_update("health", {
        "league_manager": "HEALTHY",
        "REF01": "HEALTHY",
        "REF02": "HEALTHY",
        "P01": "HEALTHY",
        "P02": "HEALTHY"
    })

    await dashboard.broadcast_update("standings", [
        {"rank": 1, "player_id": "P01", "points": 6, "wins": 2, "losses": 0, "draws": 0},
        {"rank": 2, "player_id": "P02", "points": 3, "wins": 1, "losses": 1, "draws": 0}
    ])

    print("Dashboard started successfully!")
    print("Open http://localhost:9000 in your browser")
    print()

    # Run dashboard server
    await dashboard.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDashboard stopped")
