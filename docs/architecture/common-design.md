# Common Design Patterns

**Document Type:** Architecture Design
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** All Agent Developers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [MCP Server Pattern](#2-mcp-server-pattern)
3. [JSON-RPC 2.0 Communication](#3-json-rpc-20-communication)
4. [Tool Registration Pattern](#4-tool-registration-pattern)
5. [Error Handling Hierarchy](#5-error-handling-hierarchy)
6. [Retry Logic with Exponential Backoff](#6-retry-logic-with-exponential-backoff)
7. [Circuit Breaker Pattern](#7-circuit-breaker-pattern)
8. [Structured Logging](#8-structured-logging)
9. [Timeout Management](#9-timeout-management)
10. [Integration Examples](#10-integration-examples)

---

## 1. Introduction

This document defines common design patterns used across **all agents** in the Even/Odd Game League system:
- League Manager
- Referees
- Player Agents

### 1.1 Core Principles

1. **Uniformity:** All agents use identical patterns for HTTP servers, logging, error handling
2. **Resilience:** Retry logic, circuit breakers, timeout enforcement
3. **Observability:** Structured logging in JSON Lines format
4. **Simplicity:** Minimal dependencies, clear interfaces

### 1.2 Technology Stack

- **Language:** Python 3.11+
- **HTTP Framework:** FastAPI (async support)
- **Protocol:** JSON-RPC 2.0 over HTTP
- **Logging:** JSON Lines (.jsonl)
- **Data Format:** JSON (for config and data files)

---

## 2. MCP Server Pattern

All agents implement an HTTP server exposing MCP tools via JSON-RPC 2.0.

### 2.1 Base Server Template

**File:** `src/common/mcp_server.py`

```python
"""
Base MCP Server Template
All agents (League Manager, Referee, Player) inherit from this class.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from typing import Callable, Dict, Any, Optional
import uvicorn
import logging

class MCPServer:
    """
    Base class for all MCP servers in the system.

    Usage:
        server = MCPServer(agent_id="P01", port=8101)
        server.register_tool("handle_game_invitation", handle_invitation)
        server.run()
    """

    def __init__(self, agent_id: str, port: int):
        self.agent_id = agent_id
        self.port = port
        self.app = FastAPI(title=f"MCP Server - {agent_id}")
        self.tool_handlers: Dict[str, Callable] = {}

        # Setup routes
        self.app.post("/mcp")(self.mcp_endpoint)
        self.app.get("/health")(self.health_check)
        self.app.post("/initialize")(self.initialize)

    def register_tool(self, method_name: str, handler: Callable):
        """Register an MCP tool handler."""
        self.tool_handlers[method_name] = handler
        logging.info(f"Registered tool: {method_name}")

    async def mcp_endpoint(self, request: Request):
        """
        Main JSON-RPC 2.0 endpoint.
        All MCP tool calls route through here.
        """
        try:
            body = await request.json()
        except Exception as e:
            return self._jsonrpc_error(-32700, "Parse error", request_id=None)

        # Validate JSON-RPC 2.0 structure
        jsonrpc = body.get("jsonrpc")
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")

        if jsonrpc != "2.0":
            return self._jsonrpc_error(-32600, "Invalid Request", request_id)

        if not method:
            return self._jsonrpc_error(-32600, "Missing method", request_id)

        # Route to handler
        if method not in self.tool_handlers:
            return self._jsonrpc_error(-32601, f"Method not found: {method}", request_id)

        try:
            result = await self.tool_handlers[method](params)
            return {
                "jsonrpc": "2.0",
                "result": result,
                "id": request_id
            }
        except ValidationError as e:
            return self._jsonrpc_error(-32602, f"Invalid params: {str(e)}", request_id)
        except Exception as e:
            logging.error(f"Tool execution error: {str(e)}", exc_info=True)
            return self._jsonrpc_error(-32603, f"Internal error: {str(e)}", request_id)

    async def health_check(self):
        """Health check endpoint."""
        return {
            "status": "healthy",
            "agent_id": self.agent_id,
            "port": self.port,
            "tools": list(self.tool_handlers.keys())
        }

    async def initialize(self, request: Request):
        """
        MCP initialization handshake.
        Required by MCP protocol.
        """
        body = await request.json()
        return {
            "jsonrpc": "2.0",
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": f"even-odd-agent-{self.agent_id}",
                    "version": "1.0.0"
                }
            },
            "id": body.get("id", 1)
        }

    def _jsonrpc_error(self, code: int, message: str, request_id: Optional[int]):
        """Create JSON-RPC 2.0 error response."""
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": code,
                "message": message
            },
            "id": request_id
        }

    def run(self):
        """Start the server."""
        logging.info(f"Starting MCP server for {self.agent_id} on port {self.port}")
        uvicorn.run(self.app, host="0.0.0.0", port=self.port)
```

### 2.2 Usage Example

**Player Agent Implementation:**

```python
from mcp_server import MCPServer
from handlers import handle_game_invitation, choose_parity, notify_match_result

def main():
    # Create server
    server = MCPServer(agent_id="P01", port=8101)

    # Register tools
    server.register_tool("handle_game_invitation", handle_game_invitation)
    server.register_tool("choose_parity", choose_parity)
    server.register_tool("notify_match_result", notify_match_result)

    # Start server
    server.run()

if __name__ == "__main__":
    main()
```

---

## 3. JSON-RPC 2.0 Communication

All inter-agent communication uses JSON-RPC 2.0 over HTTP.

### 3.1 Request Structure

```json
{
  "jsonrpc": "2.0",
  "method": "choose_parity",
  "params": {
    "protocol": "league.v2",
    "message_type": "CHOOSE_PARITY_CALL",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:15:05Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_ref01_abc123",
    "match_id": "R1M1",
    "player_id": "P01"
  },
  "id": 1101
}
```

### 3.2 Response Structure

**Success:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "CHOOSE_PARITY_RESPONSE",
    "sender": "player:P01",
    "timestamp": "20250115T10:15:10Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_p01_xyz789",
    "match_id": "R1M1",
    "player_id": "P01",
    "parity_choice": "even"
  },
  "id": 1101
}
```

**Error:**

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params: missing match_id"
  },
  "id": 1101
}
```

### 3.3 Client Implementation

**File:** `src/common/mcp_client.py`

```python
"""
MCP Client for making JSON-RPC 2.0 requests.
"""

import httpx
import logging
from typing import Dict, Any, Optional

class MCPClient:
    """Client for calling MCP tools on remote agents."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.client = httpx.AsyncClient(timeout=timeout)

    async def call_tool(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any],
        request_id: int = 1
    ) -> Dict[str, Any]:
        """
        Call an MCP tool on a remote agent.

        Args:
            endpoint: HTTP endpoint (e.g., "http://localhost:8001/mcp")
            method: Tool name (e.g., "choose_parity")
            params: Tool parameters (must include message envelope)
            request_id: JSON-RPC request ID

        Returns:
            Response dictionary (either result or error)

        Raises:
            httpx.TimeoutException: If request times out
            httpx.HTTPError: If HTTP error occurs
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": request_id
        }

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            logging.error(f"Timeout calling {method} on {endpoint}")
            raise
        except httpx.HTTPError as e:
            logging.error(f"HTTP error calling {method}: {str(e)}")
            raise

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
```

---

## 4. Tool Registration Pattern

All MCP tools use a decorator-based registration pattern.

### 4.1 Decorator Implementation

```python
"""
Decorator for registering MCP tools.
"""

from functools import wraps
from pydantic import BaseModel, ValidationError
import logging

def mcp_tool(request_schema: BaseModel = None, response_schema: BaseModel = None):
    """
    Decorator for MCP tool handlers.

    Usage:
        @mcp_tool(request_schema=ChooseParityRequest, response_schema=ChooseParityResponse)
        async def choose_parity(params: dict) -> dict:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(params: dict) -> dict:
            # Validate request
            if request_schema:
                try:
                    validated_params = request_schema(**params)
                    params = validated_params.dict()
                except ValidationError as e:
                    logging.error(f"Request validation failed: {str(e)}")
                    raise

            # Execute handler
            result = await func(params)

            # Validate response
            if response_schema:
                try:
                    validated_result = response_schema(**result)
                    result = validated_result.dict()
                except ValidationError as e:
                    logging.error(f"Response validation failed: {str(e)}")
                    raise

            return result

        return wrapper
    return decorator
```

### 4.2 Usage Example

```python
from pydantic import BaseModel
from decorators import mcp_tool

class ChooseParityRequest(BaseModel):
    protocol: str
    message_type: str
    match_id: str
    player_id: str

class ChooseParityResponse(BaseModel):
    protocol: str
    message_type: str
    match_id: str
    player_id: str
    parity_choice: str  # "even" or "odd"

@mcp_tool(request_schema=ChooseParityRequest, response_schema=ChooseParityResponse)
async def choose_parity(params: dict) -> dict:
    """Handle parity choice request."""
    match_id = params["match_id"]

    # Strategy logic here
    choice = "even"  # Simplified

    return {
        "protocol": "league.v2",
        "message_type": "CHOOSE_PARITY_RESPONSE",
        "match_id": match_id,
        "player_id": params["player_id"],
        "parity_choice": choice
    }
```

---

## 5. Error Handling Hierarchy

All agents use a consistent error handling hierarchy.

### 5.1 Error Categories

**Table: Error Code Categories**

| Category | Code Range | Severity | Action |
|----------|------------|----------|--------|
| Protocol Errors | E001-E009 | Medium | Retry |
| Authentication | E010-E019 | High | Re-authenticate |
| Validation | E020-E029 | High | Fix request |
| Game Logic | E030-E039 | Medium | Retry or forfeit |
| System Errors | E090-E099 | Critical | Alert admin |

### 5.2 Error Handler Implementation

```python
"""
Centralized error handling.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ErrorCode(Enum):
    TIMEOUT_ERROR = "E001"
    INVALID_CHOICE = "E002"
    PLAYER_NO_SHOW = "E003"
    AUTH_TOKEN_INVALID = "E012"
    PROTOCOL_VERSION_MISMATCH = "E021"
    INTERNAL_SERVER_ERROR = "E099"

@dataclass
class GameError:
    code: ErrorCode
    description: str
    context: Optional[dict] = None
    retryable: bool = False

def handle_error(error: GameError, conversation_id: str) -> dict:
    """
    Convert GameError to LEAGUE_ERROR or GAME_ERROR message.

    Returns:
        Error message dict (follows protocol)
    """
    return {
        "protocol": "league.v2",
        "message_type": "GAME_ERROR",
        "conversation_id": conversation_id,
        "error_code": error.code.value,
        "error_description": error.description,
        "context": error.context or {},
        "retryable": error.retryable
    }
```

### 5.3 Error Response Example

```python
from errors import GameError, ErrorCode, handle_error

async def choose_parity(params: dict) -> dict:
    try:
        # Validate timeout
        deadline = params.get("deadline")
        if is_past_deadline(deadline):
            error = GameError(
                code=ErrorCode.TIMEOUT_ERROR,
                description="Request exceeded deadline",
                context={"deadline": deadline},
                retryable=True
            )
            raise Exception(handle_error(error, params["conversation_id"]))

        # Normal processing
        return {"parity_choice": "even"}

    except Exception as e:
        logging.error(f"Error in choose_parity: {str(e)}")
        raise
```

---

## 6. Retry Logic with Exponential Backoff

All agents implement retry logic for transient failures.

### 6.1 Retry Configuration

```python
"""
Retry configuration and implementation.
"""

from dataclasses import dataclass
import time
import logging
from typing import Callable, Any

@dataclass
class RetryConfig:
    max_retries: int = 3
    initial_delay: float = 2.0  # seconds
    backoff_multiplier: float = 2.0
    retryable_errors: list = None  # Error codes that should trigger retry

    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = ["E001", "E009", "E099"]

async def call_with_retry(
    func: Callable,
    config: RetryConfig,
    *args,
    **kwargs
) -> Any:
    """
    Call function with retry logic.

    Args:
        func: Async function to call
        config: Retry configuration
        *args, **kwargs: Arguments to pass to func

    Returns:
        Function result

    Raises:
        Last exception if all retries fail
    """
    last_error = None

    for attempt in range(config.max_retries):
        try:
            result = await func(*args, **kwargs)

            # Check if result contains retryable error
            if isinstance(result, dict) and "error_code" in result:
                if result["error_code"] not in config.retryable_errors:
                    return result  # Non-retryable error, return immediately
            else:
                return result  # Success

        except Exception as e:
            last_error = e
            logging.warning(f"Attempt {attempt + 1}/{config.max_retries} failed: {str(e)}")

        # Don't sleep after last attempt
        if attempt < config.max_retries - 1:
            delay = config.initial_delay * (config.backoff_multiplier ** attempt)
            logging.info(f"Retrying in {delay:.1f} seconds...")
            time.sleep(delay)

    # All retries exhausted
    if last_error:
        raise last_error
    return result  # Return last result (likely an error)
```

### 6.2 Usage Example

```python
from retry import call_with_retry, RetryConfig
from mcp_client import MCPClient

async def send_game_invitation(player_endpoint: str, params: dict):
    """Send game invitation with retry."""
    client = MCPClient(timeout=5)
    config = RetryConfig(max_retries=3, initial_delay=2.0)

    result = await call_with_retry(
        client.call_tool,
        config,
        endpoint=player_endpoint,
        method="handle_game_invitation",
        params=params
    )

    return result
```

---

## 7. Circuit Breaker Pattern

Circuit breaker prevents cascading failures.

### 7.1 Implementation

```python
"""
Circuit Breaker implementation.
"""

from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Failures exceed threshold
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    reset_timeout: int = 60  # seconds
    success_threshold: int = 2  # Successes needed in HALF_OPEN to close

class CircuitBreaker:
    """
    Circuit breaker for protecting against cascading failures.

    Usage:
        breaker = CircuitBreaker("player:P01")
        if breaker.can_execute():
            result = await call_player_tool()
            breaker.record_success()
        else:
            # Circuit is open, skip call
            pass
    """

    def __init__(self, name: str, config: CircuitBreakerConfig = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time: datetime = None

    def can_execute(self) -> bool:
        """Check if circuit allows execution."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if timeout expired
            if self._timeout_expired():
                logging.info(f"Circuit {self.name}: Transitioning to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
                return True
            return False

        # HALF_OPEN state
        return True

    def record_success(self):
        """Record successful execution."""
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.config.success_threshold:
                logging.info(f"Circuit {self.name}: Transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.failures = 0
                self.successes = 0
        elif self.state == CircuitState.CLOSED:
            # Reset failure count on success
            self.failures = 0

    def record_failure(self):
        """Record failed execution."""
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            logging.warning(f"Circuit {self.name}: Failure in HALF_OPEN, transitioning to OPEN")
            self.state = CircuitState.OPEN
            self.successes = 0
        elif self.state == CircuitState.CLOSED:
            self.failures += 1
            if self.failures >= self.config.failure_threshold:
                logging.error(f"Circuit {self.name}: Failure threshold exceeded, transitioning to OPEN")
                self.state = CircuitState.OPEN

    def _timeout_expired(self) -> bool:
        """Check if reset timeout has expired."""
        if not self.last_failure_time:
            return True
        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.reset_timeout
```

### 7.2 Usage Example

```python
from circuit_breaker import CircuitBreaker

class Referee:
    def __init__(self):
        self.player_circuits = {}  # player_id -> CircuitBreaker

    async def call_player_tool(self, player_id: str, method: str, params: dict):
        # Get or create circuit breaker for this player
        if player_id not in self.player_circuits:
            self.player_circuits[player_id] = CircuitBreaker(f"player:{player_id}")

        breaker = self.player_circuits[player_id]

        # Check if circuit allows execution
        if not breaker.can_execute():
            logging.warning(f"Circuit open for {player_id}, skipping call")
            return {"error": "Circuit breaker open"}

        try:
            result = await self.mcp_client.call_tool(
                endpoint=self.players[player_id]["endpoint"],
                method=method,
                params=params
            )
            breaker.record_success()
            return result
        except Exception as e:
            breaker.record_failure()
            raise
```

---

## 8. Structured Logging

All agents use JSON Lines logging format.

### 8.1 Logger Implementation

```python
"""
Structured JSON logger.
"""

import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARN = "WARN"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class JsonLogger:
    """
    JSON Lines logger for structured logging.

    Usage:
        logger = JsonLogger("P01")
        logger.info("Player registered", player_id="P01", league_id="league_2025")
    """

    def __init__(self, agent_id: str, log_file: Optional[str] = None):
        self.agent_id = agent_id
        self.log_file = log_file

    def _log(
        self,
        level: LogLevel,
        message: str,
        conversation_id: Optional[str] = None,
        **kwargs
    ):
        """Internal logging method."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.value,
            "agent_id": self.agent_id,
            "message": message
        }

        if conversation_id:
            entry["conversation_id"] = conversation_id

        # Add any additional fields
        entry.update(kwargs)

        log_line = json.dumps(entry)

        # Write to stderr (stdout used for responses)
        print(log_line, file=sys.stderr)

        # Optionally write to file
        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(log_line + '\n')

    def debug(self, message: str, **kwargs):
        self._log(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self._log(LogLevel.INFO, message, **kwargs)

    def warn(self, message: str, **kwargs):
        self._log(LogLevel.WARN, message, **kwargs)

    def error(self, message: str, **kwargs):
        self._log(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self._log(LogLevel.CRITICAL, message, **kwargs)
```

### 8.2 Usage Example

```python
from logger import JsonLogger

logger = JsonLogger("P01", log_file="SHARED/logs/agents/P01.log.jsonl")

# Log registration
logger.info(
    "Player registered",
    player_id="P01",
    league_id="league_2025_even_odd",
    display_name="Agent Alpha"
)

# Log game invitation
logger.info(
    "Game invitation received",
    conversation_id="convr1m1001",
    match_id="R1M1",
    opponent_id="P02"
)

# Log error
logger.error(
    "Timeout during choice",
    conversation_id="convr1m1001",
    match_id="R1M1",
    deadline="20250115T10:15:35Z"
)
```

### 8.3 Log Output Example

```json
{"timestamp": "2025-01-15T10:05:01Z", "level": "INFO", "agent_id": "P01", "message": "Player registered", "player_id": "P01", "league_id": "league_2025_even_odd", "display_name": "Agent Alpha"}
{"timestamp": "2025-01-15T10:15:00Z", "level": "INFO", "agent_id": "P01", "message": "Game invitation received", "conversation_id": "convr1m1001", "match_id": "R1M1", "opponent_id": "P02"}
{"timestamp": "2025-01-15T10:15:36Z", "level": "ERROR", "agent_id": "P01", "message": "Timeout during choice", "conversation_id": "convr1m1001", "match_id": "R1M1", "deadline": "20250115T10:15:35Z"}
```

---

## 9. Timeout Management

All tools enforce strict timeouts.

### 9.1 Timeout Decorator

```python
"""
Timeout enforcement decorator.
"""

import asyncio
from functools import wraps

def with_timeout(seconds: int):
    """
    Decorator to enforce timeout on async functions.

    Usage:
        @with_timeout(30)
        async def choose_parity(params: dict) -> dict:
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                logging.error(f"{func.__name__} timed out after {seconds}s")
                raise
        return wrapper
    return decorator
```

### 9.2 Usage Example

```python
from timeout import with_timeout

@with_timeout(30)  # 30 second timeout
async def choose_parity(params: dict) -> dict:
    """This function MUST complete within 30 seconds."""
    # Strategy logic here (potentially slow)
    choice = await complex_strategy_computation()
    return {"parity_choice": choice}
```

---

## 10. Integration Examples

### 10.1 Complete Player Agent

```python
"""
Complete player agent using all common patterns.
"""

from mcp_server import MCPServer
from logger import JsonLogger
from timeout import with_timeout
from retry import call_with_retry, RetryConfig

# Initialize
logger = JsonLogger("P01")
server = MCPServer("P01", port=8101)

# Tool handlers
@with_timeout(5)
async def handle_game_invitation(params: dict) -> dict:
    logger.info(
        "Invitation received",
        conversation_id=params["conversation_id"],
        match_id=params["match_id"]
    )
    return {
        "protocol": "league.v2",
        "message_type": "GAME_JOIN_ACK",
        "match_id": params["match_id"],
        "accept": True
    }

@with_timeout(30)
async def choose_parity(params: dict) -> dict:
    logger.info(
        "Choice requested",
        conversation_id=params["conversation_id"],
        match_id=params["match_id"]
    )

    # Strategy logic (simplified)
    choice = "even"

    return {
        "protocol": "league.v2",
        "message_type": "CHOOSE_PARITY_RESPONSE",
        "match_id": params["match_id"],
        "parity_choice": choice
    }

async def notify_match_result(params: dict) -> dict:
    logger.info(
        "Match result received",
        conversation_id=params["conversation_id"],
        winner=params["game_result"]["winner_player_id"]
    )
    return {"acknowledged": True}

# Register tools
server.register_tool("handle_game_invitation", handle_game_invitation)
server.register_tool("choose_parity", choose_parity)
server.register_tool("notify_match_result", notify_match_result)

# Run server
if __name__ == "__main__":
    server.run()
```

---

## Summary

This document defines 9 common design patterns used across all agents:

1. ✅ **MCP Server Pattern** - Uniform FastAPI-based HTTP server
2. ✅ **JSON-RPC 2.0 Communication** - Standard request/response structure
3. ✅ **Tool Registration Pattern** - Decorator-based tool registration
4. ✅ **Error Handling Hierarchy** - Consistent error codes and handling
5. ✅ **Retry Logic** - Exponential backoff for transient failures
6. ✅ **Circuit Breaker** - Prevent cascading failures
7. ✅ **Structured Logging** - JSON Lines format for observability
8. ✅ **Timeout Management** - Strict timeout enforcement
9. ✅ **Integration Examples** - Complete working examples

All agents (League Manager, Referee, Player) MUST implement these patterns for consistency and reliability.

---

**Related Documents:**
- `message-envelope-design.md` - Message structure specification
- `authentication-design.md` - Token-based auth system
- `state-management-design.md` - State machine patterns
- `player-agent-architecture.md` - Player-specific implementation
- `referee-architecture.md` - Referee-specific implementation
- `league-manager-architecture.md` - League Manager implementation

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
