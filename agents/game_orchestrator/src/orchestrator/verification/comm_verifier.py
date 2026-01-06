"""
Communication Verifier - Test connectivity and protocol compliance.

Verifies agents can communicate via JSON-RPC 2.0.
"""

import asyncio
from typing import Dict
from pydantic import BaseModel
import httpx
from loguru import logger

from ..config import AgentConfig


class VerificationResult(BaseModel):
    """Result of communication verification."""
    success: bool
    reachable: bool
    protocol_compliant: bool
    error: str = ""


class CommunicationVerifier:
    """Verifies agent communication and protocol compliance."""

    def __init__(self, agents: Dict[str, AgentConfig]):
        """
        Initialize communication verifier.

        Args:
            agents: Dictionary mapping agent_id to AgentConfig
        """
        self.agents = agents

    async def verify_agent(
        self, agent_id: str, endpoint: str
    ) -> VerificationResult:
        """
        Verify communication with a single agent.

        Args:
            agent_id: Agent identifier
            endpoint: MCP endpoint URL (e.g., http://localhost:8000/mcp)

        Returns:
            VerificationResult with verification status
        """
        logger.info(f"Verifying agent {agent_id}", endpoint=endpoint)

        # Check reachability
        reachable = await self._check_reachability(endpoint)
        if not reachable:
            return VerificationResult(
                success=False,
                reachable=False,
                protocol_compliant=False,
                error="Agent not reachable"
            )

        # Check protocol compliance
        compliant, error = await self._check_protocol(endpoint)

        return VerificationResult(
            success=compliant,
            reachable=True,
            protocol_compliant=compliant,
            error=error
        )

    async def verify_all_agents(self) -> Dict[str, VerificationResult]:
        """
        Verify communication with all agents.

        Returns:
            Dictionary mapping agent_id to VerificationResult
        """
        results = {}

        for agent_id, config in self.agents.items():
            # Convert health endpoint to MCP endpoint
            mcp_endpoint = config.health_endpoint.replace(
                "/health", "/mcp"
            )
            results[agent_id] = await self.verify_agent(
                agent_id, mcp_endpoint
            )

        return results

    async def _check_reachability(self, endpoint: str) -> bool:
        """Check if endpoint is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Try health endpoint first
                health_endpoint = endpoint.replace("/mcp", "/health")
                response = await client.get(health_endpoint)
                return response.status_code == 200
        except Exception as e:
            logger.debug(f"Reachability check failed", error=str(e))
            return False

    async def _check_protocol(self, endpoint: str) -> tuple[bool, str]:
        """
        Check JSON-RPC 2.0 protocol compliance.

        Returns:
            Tuple of (compliant, error_message)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Send initialize request to /initialize endpoint
                initialize_endpoint = endpoint.replace("/mcp", "/initialize")
                logger.info(f"Sending initialize to {initialize_endpoint}")
                response = await client.post(
                    initialize_endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "clientInfo": {
                                "name": "orchestrator",
                                "version": "1.0.0"
                            }
                        },
                        "id": 1
                    }
                )

                logger.info(
                    f"Initialize response",
                    status=response.status_code,
                    endpoint=initialize_endpoint
                )

                if response.status_code != 200:
                    logger.error(f"Bad HTTP status", status=response.status_code)
                    return False, f"HTTP {response.status_code}"

                logger.debug(f"Response text: {response.text[:500]}")
                data = response.json()
                logger.info(f"Response keys: {list(data.keys())}")

                # Verify JSON-RPC 2.0 response
                if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
                    logger.error(
                        "Invalid JSON-RPC response",
                        has_jsonrpc="jsonrpc" in data,
                        version=data.get("jsonrpc"),
                        data=data
                    )
                    return False, f"Invalid JSON-RPC version: {data.get('jsonrpc')}"

                if "result" not in data:
                    logger.error(
                        "Missing result field",
                        keys=list(data.keys()),
                        data=data
                    )
                    return False, "Missing result field"

                logger.info("Protocol compliance verified", endpoint=endpoint)
                return True, ""

        except Exception as e:
            return False, f"Protocol check failed: {str(e)}"
