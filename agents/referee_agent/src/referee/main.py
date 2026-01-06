"""
Referee agent entry point.

Starts the MCP server and handles registration with League Manager.
"""

import asyncio
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import config
from .utils import setup_logger, logger
from .server import RefereeServer
from .mcp_client import MCPClient
from .utils import get_utc_timestamp
from .match_poller import match_polling_loop


async def register_to_league():
    """
    Register referee with League Manager.

    Sends REFEREE_REGISTER_REQUEST and stores credentials.
    """
    logger.info("Registering with League Manager")

    client = MCPClient(timeout=10)
    try:
        response = await client.call_tool(
            config.league_manager_endpoint,
            "register_referee",
            {
                "protocol": "league.v2",
                "message_type": "REFEREE_REGISTER_REQUEST",
                "sender": f"referee:{config.referee_id}",
                "timestamp": get_utc_timestamp(),
                "conversation_id": f"convrefalphareg001",
                "referee_meta": {
                    "display_name": config.referee_display_name,
                    "version": "1.0.0",
                    "game_types": ["even_odd"],
                    "contact_endpoint": (
                        f"http://localhost:{config.referee_port}/mcp"
                    ),
                    "max_concurrent_matches": config.max_concurrent_matches
                }
            }
        )

        # Debug: log full response
        logger.debug("Registration response received", response=response)

        result = response.get("result", {})

        # Handle both direct response and wrapped response
        if isinstance(result, dict) and result.get("status") == "ACCEPTED":
            config.set_credentials(
                referee_id=result["referee_id"],
                auth_token=result["auth_token"],
                league_id=result["league_id"]
            )
            logger.info(
                "Registration successful",
                referee_id=result.get("referee_id")
            )
        elif isinstance(response, dict) and response.get("status") == "ACCEPTED":
            # Direct response without JSON-RPC wrapper
            config.set_credentials(
                referee_id=response["referee_id"],
                auth_token=response["auth_token"],
                league_id=response["league_id"]
            )
            logger.info(
                "Registration successful",
                referee_id=response.get("referee_id")
            )
        else:
            logger.error(
                "Registration rejected",
                result=result,
                response=response
            )
    except Exception as e:
        logger.error(
            "Registration failed",
            error=str(e),
            exc_info=True
        )
    finally:
        await client.close()


@asynccontextmanager
async def lifespan(app_instance: FastAPI):
    """Manage application lifecycle and registration."""
    # Startup: Wait for server to be ready, then register and start polling
    await asyncio.sleep(2)  # Give server time to fully start
    asyncio.create_task(register_to_league())
    asyncio.create_task(match_polling_loop())
    yield
    # Shutdown: cleanup if needed


# Create server at module level for uvicorn
server = RefereeServer()

# Add lifespan to trigger registration after startup
server.app.router.lifespan_context = lifespan

# Export app for uvicorn
app = server.app


def main():
    """
    Main entry point for referee agent.

    Initializes logging, creates server, and starts listening
    for match assignments.
    """
    # Setup logging
    setup_logger(config.referee_id)

    logger.info(
        "Starting Referee Agent",
        referee_id=config.referee_id,
        port=config.referee_port
    )

    # Start server (registration will happen automatically after startup)
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=config.referee_port,
        log_level="info"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Referee Agent")
    parser.add_argument(
        "--port",
        type=int,
        help="Port to run the referee server on"
    )
    args = parser.parse_args()

    # Override config port if provided
    if args.port:
        config.referee_port = args.port

    main()
