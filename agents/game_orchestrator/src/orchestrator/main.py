"""
Game Orchestrator - Master controller for tournament system.

Coordinates startup, monitoring, and tournament execution across all agents.
"""

import asyncio
import signal
from loguru import logger

from .config import Config
from .lifecycle.agent_manager import AgentLifecycleManager
from .monitoring.health_monitor import HealthMonitor
from .verification.comm_verifier import CommunicationVerifier
from .tournament.controller import TournamentController
from .dashboard.server import DashboardServer
from .recovery.error_manager import ErrorRecoveryManager
from .logging_utils.log_aggregator import LogAggregator
from .startup import StartupCoordinator
from .tournament_monitor import TournamentMonitor
from .recovery_setup import RecoverySetup
from .cleanup import CleanupCoordinator


class GameOrchestrator:
    """Master controller for the tournament system."""

    def __init__(self, config_path: str):
        """
        Initialize Game Orchestrator.

        Args:
            config_path: Path to agents.json configuration file
        """
        logger.info("Initializing Game Orchestrator", config=config_path)

        # Load configuration
        self.config = Config(config_path)

        # Initialize components
        self.lifecycle = AgentLifecycleManager(self.config.agents)
        self.health = HealthMonitor(
            self.config.agents,
            check_interval=self.config.orchestrator.health_check_interval
        )
        self.verifier = CommunicationVerifier(self.config.agents)

        # Get league manager endpoint
        league_mgr = self.config.get_agents_by_type("LEAGUE_MANAGER")[0]
        league_endpoint = league_mgr.health_endpoint.replace("/health", "/mcp")
        self.tournament = TournamentController(
            league_endpoint,
            auto_start=self.config.orchestrator.auto_start,
            registration_timeout=self.config.orchestrator.registration_timeout,
            min_players=self.config.orchestrator.min_players,
            min_referees=self.config.orchestrator.min_referees
        )

        # Create dashboard with tournament controller
        self.dashboard = DashboardServer(
            port=self.config.orchestrator.dashboard_port,
            tournament_controller=self.tournament
        )
        self.recovery = ErrorRecoveryManager()
        self.logs = LogAggregator("SHARED/logs/agents")

        # Shutdown tracking
        self.shutdown_requested = False
        self.dashboard_task = None

        # Setup coordinators
        self.startup = StartupCoordinator(self)
        self.monitor = TournamentMonitor(self)
        self.cleanup = CleanupCoordinator(self)

        # Setup recovery handlers and signal handlers
        RecoverySetup(self).setup_handlers()
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        def handle_shutdown_signal(signum, frame):
            signal_name = signal.Signals(signum).name
            logger.warning(f"Received {signal_name} - initiating graceful shutdown")
            self.shutdown_requested = True

        signal.signal(signal.SIGTERM, handle_shutdown_signal)
        signal.signal(signal.SIGINT, handle_shutdown_signal)

    async def run(self) -> bool:
        """
        Execute complete orchestrator flow.

        Returns:
            True if orchestrator completed successfully
        """
        try:
            # Execute startup sequence
            if not await self.startup.execute_startup_sequence():
                return False

            # Start health monitoring
            logger.info("=== Stage 5: Starting Health Monitoring ===")
            await self.health.start()

            # Start dashboard
            logger.info("=== Stage 6: Starting Dashboard ===")
            self.dashboard_task = asyncio.create_task(self.dashboard.start())
            await asyncio.sleep(2)

            # Wait for registrations
            logger.info("=== Stage 7: Waiting for Registrations ===")
            if not await self.tournament.wait_for_registrations():
                logger.error("Registration failed or timed out")
                return False

            logger.info("All agents registered successfully")

            # Start tournament if auto-start enabled
            if self.tournament.auto_start:
                logger.info("=== Stage 8: Auto-starting Tournament ===")
                if not await self.tournament.start_tournament():
                    logger.error("Failed to start tournament")
                    return False

                # Monitor tournament execution
                await self.monitor.monitor_until_complete()
            else:
                logger.info("Auto-start disabled. Waiting for manual start.")

            return True

        except Exception as e:
            logger.critical("Orchestrator failed", error=str(e))
            return False

        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup and shutdown all components."""
        await self.cleanup.execute_shutdown()


if __name__ == "__main__":
    from .cli import main
    main()
