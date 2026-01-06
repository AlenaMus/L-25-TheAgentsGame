# Product Requirements Document (PRD)
# Implementation Architecture & Technical Patterns

**Document Version:** 1.0
**Date:** 2025-12-20
**Status:** Draft
**Product Owner:** AI Development Course Team
**Target Release:** Phase 1 - Foundation
**Related Documents:**
- `league-system-prd.md` (League Management System)
- `even-odd-game-prd.md` (Even/Odd Game Rules)
- `game-protocol-messages-prd.md` (Protocol Messages)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [System Architecture](#system-architecture)
3. [MCP Server Implementation](#mcp-server-implementation)
4. [Component Implementation Requirements](#component-implementation-requirements)
5. [HTTP Communication Patterns](#http-communication-patterns)
6. [State Management](#state-management)
7. [Error Handling & Resilience](#error-handling--resilience)
8. [Structured Logging](#structured-logging)
9. [Authentication & Security](#authentication--security)
10. [Local Testing & Deployment](#local-testing--deployment)
11. [Implementation Best Practices](#implementation-best-practices)
12. [User Stories](#user-stories)
13. [Acceptance Criteria](#acceptance-criteria)
14. [Success Metrics](#success-metrics)

---

## 1. Executive Summary

### 1.1 Problem Statement
Students need clear implementation guidance to build agents that communicate via MCP (Model Context Protocol) over HTTP using JSON-RPC 2.0. Without standardized patterns for error handling, logging, and resilience, agents will fail unpredictably in the distributed tournament environment.

### 1.2 Solution Overview
Define a comprehensive implementation architecture with:
- **FastAPI-based MCP servers** for all components (League, Referee, Player)
- **Standardized HTTP communication** patterns with retry logic
- **Structured JSON logging** for debugging distributed systems
- **Token-based authentication** for security
- **Circuit breaker patterns** for resilience
- **Local testing procedures** for development

### 1.3 Key Benefits
- **Rapid Development**: Students can start from working templates
- **Reliability**: Built-in retry and circuit breaker patterns prevent cascading failures
- **Debuggability**: Structured logging enables quick issue diagnosis
- **Consistency**: All agents use same patterns, ensuring interoperability
- **Educational Value**: Students learn production-grade distributed systems patterns

---

## 2. System Architecture

### 2.1 Component Topology

```
┌──────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR / HOST                    │
│              (Coordinates all components)                 │
└──────────────────────────────────────────────────────────┘
                            ↓ HTTP
┌──────────────────────────────────────────────────────────┐
│                   LEAGUE MANAGER                          │
│                   Port: 8000                              │
│                   FastAPI + MCP Server                    │
└──────────────────────────────────────────────────────────┘
                            ↓ HTTP
┌──────────────────────────────────────────────────────────┐
│                      REFEREE(S)                           │
│                   Ports: 8001-8010                        │
│                   FastAPI + MCP Server                    │
└──────────────────────────────────────────────────────────┘
                            ↓ HTTP
┌──────────────────────────────────────────────────────────┐
│                    PLAYER AGENTS                          │
│                   Ports: 8101-8150                        │
│                   FastAPI + MCP Server                    │
└──────────────────────────────────────────────────────────┘
```

**Communication Flow:**
- **Orchestrator → League Manager**: Tournament control (start, stop, query)
- **League Manager → Referees**: Match assignments
- **League Manager → Players**: Round announcements, standings updates
- **Referees → Players**: Game invitations, move requests, results
- **Players → Referees**: Move responses, acknowledgments
- **Referees → League Manager**: Match result reports

---

### 2.2 Orchestrator Role

**Purpose:** Coordinate the lifecycle of all agents and manage tournament flow.

**Responsibilities:**
1. **Startup Coordination**:
   - Start League Manager first (port 8000)
   - Start Referee(s) second (ports 8001-8010)
   - Start Players last (ports 8101-8150)

2. **Registration Orchestration**:
   - Trigger referee registration with League Manager
   - Trigger player registration with League Manager
   - Verify all registrations succeed before starting tournament

3. **Tournament Management**:
   - Send start signal to League Manager
   - Monitor tournament progress
   - Handle shutdown gracefully

4. **Health Monitoring**:
   - Periodic health checks to all components
   - Restart failed components if needed
   - Aggregate logs for debugging

**Implementation Note:** The orchestrator is NOT an MCP server itself - it's a control script that manages other MCP servers.

---

### 2.3 Port Allocation Strategy

**Table: Port Assignment by Component Type**

| Component | Port Range | Capacity | Example |
|-----------|------------|----------|---------|
| League Manager | 8000 (fixed) | 1 instance | http://localhost:8000/mcp |
| Referees | 8001-8010 | 10 instances | http://localhost:8001/mcp |
| Players | 8101-8150 | 50 instances | http://localhost:8101/mcp |

**Port Allocation Rules:**
- League Manager MUST use port 8000 (hard-coded in all agents)
- Referees use sequential ports starting from 8001
- Players use sequential ports starting from 8101
- Port conflicts detected at startup → fail fast with clear error

---

## 3. MCP Server Implementation

### 3.1 Basic FastAPI MCP Server Structure

**Purpose:** All components (League, Referee, Player) implement the same base MCP server pattern.

#### 3.1.1 Request/Response Models

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uvicorn

class MCPRequest(BaseModel):
    """Standard JSON-RPC 2.0 request format."""
    jsonrpc: str = Field(default="2.0", const=True)
    method: str = Field(..., description="MCP method name")
    params: Dict[str, Any] = Field(default_factory=dict)
    id: int = Field(default=1, description="Request ID for correlation")

class MCPResponse(BaseModel):
    """Standard JSON-RPC 2.0 response format."""
    jsonrpc: str = Field(default="2.0", const=True)
    result: Dict[str, Any] = Field(default_factory=dict)
    id: int = Field(default=1)

class MCPError(BaseModel):
    """Standard JSON-RPC 2.0 error format."""
    jsonrpc: str = Field(default="2.0", const=True)
    error: Dict[str, Any] = Field(...)
    id: int = Field(default=1)
```

#### 3.1.2 Base MCP Server Template

```python
app = FastAPI(title="MCP Server", version="1.0.0")

# Tool registry: maps method names to handler functions
TOOL_HANDLERS = {}

def register_tool(method_name: str):
    """Decorator to register MCP tool handlers."""
    def decorator(func):
        TOOL_HANDLERS[method_name] = func
        return func
    return decorator

@app.post("/mcp")
async def mcp_endpoint(request: MCPRequest) -> MCPResponse:
    """
    Main MCP endpoint - routes requests to appropriate handlers.
    """
    method = request.method
    params = request.params

    # Check if method exists
    if method not in TOOL_HANDLERS:
        return MCPError(
            error={
                "code": -32601,
                "message": f"Method not found: {method}",
                "data": {"available_methods": list(TOOL_HANDLERS.keys())}
            },
            id=request.id
        ).dict()

    try:
        # Call handler
        result = await TOOL_HANDLERS[method](params)
        return MCPResponse(result=result, id=request.id)

    except Exception as e:
        return MCPError(
            error={
                "code": -32603,
                "message": "Internal error",
                "data": {"exception": str(e)}
            },
            id=request.id
        ).dict()

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8101)
```

---

### 3.2 Tool Registration Pattern

**User Story:**
> **As a** developer
> **I want to** register MCP tools using decorators
> **So that** my code is clean and maintainable

**Example:**
```python
@register_tool("handle_game_invitation")
async def handle_invitation(params: dict) -> dict:
    """Handle game invitation."""
    return {
        "message_type": "GAME_JOIN_ACK",
        "match_id": params["match_id"],
        "accept": True
    }

@register_tool("choose_parity")
async def choose_parity(params: dict) -> dict:
    """Choose even or odd."""
    import random
    return {
        "message_type": "CHOOSE_PARITY_RESPONSE",
        "parity_choice": random.choice(["even", "odd"])
    }
```

**Acceptance Criteria:**
- ✅ Tools registered via decorator pattern
- ✅ Method names match protocol specification exactly
- ✅ Handler functions async (for scalability)
- ✅ Unknown methods return JSON-RPC error -32601

---

## 4. Component Implementation Requirements

### 4.1 Player Agent Implementation

#### 4.1.1 Required Tools (Minimum)

**Mandatory Tools:** Player MUST implement exactly these 3 tools:

1. **handle_game_invitation**
   - **Input:** `{match_id, game_type, opponent_id, role_in_match, conversation_id}`
   - **Output:** `{message_type: "GAME_JOIN_ACK", accept: true/false}`
   - **Timeout:** 5 seconds
   - **Purpose:** Acknowledge match invitation

2. **choose_parity**
   - **Input:** `{match_id, player_id, context: {opponent_id, round_id, your_standings}}`
   - **Output:** `{message_type: "CHOOSE_PARITY_RESPONSE", parity_choice: "even"|"odd"}`
   - **Timeout:** 30 seconds
   - **Purpose:** Make strategic choice

3. **notify_match_result**
   - **Input:** `{match_id, game_result: {status, winner, choices, drawn_number}}`
   - **Output:** `{status: "ok"}`
   - **Timeout:** 5 seconds (best-effort)
   - **Purpose:** Receive and store game result

#### 4.1.2 Complete Player Agent Template

```python
import random
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any, List

app = FastAPI(title="Player Agent")

# State storage
class PlayerState:
    def __init__(self, player_id: str):
        self.player_id = player_id
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.match_history: List[Dict] = []

    def record_result(self, result: Dict):
        """Store match result for learning."""
        self.match_history.append(result)

        status = result.get("game_result", {}).get("status")
        winner = result.get("game_result", {}).get("winner_player_id")

        if status == "WIN" and winner == self.player_id:
            self.wins += 1
        elif status == "WIN" and winner != self.player_id:
            self.losses += 1
        elif status == "DRAW":
            self.draws += 1

# Global state (in production, use database)
state = PlayerState("P01")

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    method = request.get("method")
    params = request.get("params", {})

    if method == "handle_game_invitation":
        return handle_invitation(params)
    elif method == "choose_parity":
        return choose_parity(params)
    elif method == "notify_match_result":
        return handle_result(params)

    return {"error": "Unknown method"}

def handle_invitation(params: dict) -> dict:
    """Accept all game invitations."""
    return {
        "jsonrpc": "2.0",
        "result": {
            "message_type": "GAME_JOIN_ACK",
            "match_id": params.get("match_id"),
            "player_id": state.player_id,
            "arrival_timestamp": datetime.now(timezone.utc).isoformat(),
            "accept": True
        },
        "id": 1
    }

def choose_parity(params: dict) -> dict:
    """
    Strategy: Random choice (baseline).

    TODO: Implement adaptive strategy using match_history.
    """
    choice = random.choice(["even", "odd"])

    return {
        "jsonrpc": "2.0",
        "result": {
            "message_type": "CHOOSE_PARITY_RESPONSE",
            "match_id": params.get("match_id"),
            "player_id": params.get("player_id"),
            "parity_choice": choice
        },
        "id": 1
    }

def handle_result(params: dict) -> dict:
    """Store result for learning."""
    state.record_result(params)

    print(f"[RESULT] W:{state.wins} L:{state.losses} D:{state.draws}")

    return {
        "jsonrpc": "2.0",
        "result": {"status": "ok"},
        "id": 1
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8101)
```

**Acceptance Criteria:**
- ✅ All 3 tools implemented
- ✅ handle_invitation returns accept=true within 5s
- ✅ choose_parity returns valid choice ("even" or "odd") within 30s
- ✅ notify_match_result stores data for future strategy
- ✅ Server runs on port 8101 (or specified port)

---

### 4.2 Referee Implementation

#### 4.2.1 Required Tools

1. **register_to_league** (internal, called at startup)
2. **start_match** (triggered by League Manager)
3. **collect_choices** (internal, orchestrates player requests)
4. **draw_number** (internal, cryptographically secure random)
5. **determine_winner** (internal, applies game rules)
6. **finalize_match** (internal, reports to League Manager)

#### 4.2.2 Referee Registration Logic

```python
import requests
from typing import Optional

def register_to_league(
    league_endpoint: str = "http://localhost:8000/mcp",
    referee_name: str = "Referee Alpha",
    referee_port: int = 8001
) -> Optional[str]:
    """
    Register referee with League Manager at startup.

    Returns:
        referee_id if successful, None otherwise
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "register_referee",
        "params": {
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_REQUEST",
            "sender": f"referee:{referee_name}",
            "referee_meta": {
                "display_name": referee_name,
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": f"http://localhost:{referee_port}/mcp",
                "max_concurrent_matches": 2
            }
        },
        "id": 1
    }

    try:
        response = requests.post(league_endpoint, json=payload, timeout=10)
        result = response.json().get("result", {})

        if result.get("status") == "ACCEPTED":
            referee_id = result["referee_id"]
            print(f"✓ Registered as {referee_id}")
            return referee_id
        else:
            print(f"✗ Registration rejected: {result.get('reason')}")
            return None

    except Exception as e:
        print(f"✗ Registration failed: {e}")
        return None
```

#### 4.2.3 Winner Determination Logic

```python
import secrets
from typing import Dict, Any

def draw_number() -> int:
    """
    Draw cryptographically secure random number between 1-10.

    CRITICAL: Must use secrets module, not random module.
    """
    return secrets.randbelow(10) + 1

def determine_winner(
    choice_a: str,
    choice_b: str,
    number: int,
    player_a_id: str,
    player_b_id: str
) -> Dict[str, Any]:
    """
    Determine match outcome based on Even/Odd rules.

    Args:
        choice_a: Player A's choice ("even" or "odd")
        choice_b: Player B's choice ("even" or "odd")
        number: Drawn number (1-10)
        player_a_id: Player A's ID
        player_b_id: Player B's ID

    Returns:
        {
            "status": "WIN" | "DRAW",
            "winner": player_id or None,
            "number_parity": "even" | "odd",
            "reason": str,
            "points": {player_a_id: int, player_b_id: int}
        }
    """
    is_even = (number % 2 == 0)
    parity = "even" if is_even else "odd"

    a_correct = (choice_a == parity)
    b_correct = (choice_b == parity)

    # Case 1: Both chose same
    if choice_a == choice_b:
        return {
            "status": "DRAW",
            "winner": None,
            "number_parity": parity,
            "reason": f"Both chose {choice_a}, number was {number} ({parity})",
            "points": {player_a_id: 1, player_b_id: 1}
        }

    # Case 2: Different choices - one winner
    if a_correct:
        winner = player_a_id
    else:
        winner = player_b_id

    return {
        "status": "WIN",
        "winner": winner,
        "number_parity": parity,
        "reason": f"{winner} chose {parity}, number was {number} ({parity})",
        "points": {
            winner: 3,
            player_a_id if winner == player_b_id else player_b_id: 0
        }
    }
```

**Acceptance Criteria:**
- ✅ draw_number uses `secrets` module (not `random`)
- ✅ Winner determination follows Even/Odd rules exactly
- ✅ Draw detection: both chose same → always draw
- ✅ Points awarded correctly: Win=3, Draw=1, Loss=0

---

### 4.3 League Manager Implementation

#### 4.3.1 Required Tools

1. **register_referee** - Accept referee registrations
2. **register_player** - Accept player registrations
3. **create_schedule** - Generate round-robin schedule
4. **report_match_result** - Receive match results from referees
5. **get_standings** - Return current standings
6. **broadcast_standings** - Send standings updates to all players

#### 4.3.2 Referee Registration Handler

```python
from typing import Dict, List
from dataclasses import dataclass, field

@dataclass
class RefereeInfo:
    referee_id: str
    display_name: str
    endpoint: str
    game_types: List[str]
    max_concurrent: int

@dataclass
class PlayerInfo:
    player_id: str
    display_name: str
    endpoint: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0

class LeagueManager:
    def __init__(self):
        self.referees: Dict[str, RefereeInfo] = {}
        self.players: Dict[str, PlayerInfo] = {}
        self.next_referee_id = 1
        self.next_player_id = 1

    def register_referee(self, params: dict) -> dict:
        """
        Register a referee with the league.

        Returns:
            {status: "ACCEPTED"|"REJECTED", referee_id: str, reason: str}
        """
        referee_meta = params.get("referee_meta", {})

        # Assign ID
        referee_id = f"REF{self.next_referee_id:02d}"
        self.next_referee_id += 1

        # Store referee info
        self.referees[referee_id] = RefereeInfo(
            referee_id=referee_id,
            display_name=referee_meta.get("display_name", "Unknown"),
            endpoint=referee_meta.get("contact_endpoint"),
            game_types=referee_meta.get("game_types", []),
            max_concurrent=referee_meta.get("max_concurrent_matches", 1)
        )

        return {
            "message_type": "REFEREE_REGISTER_RESPONSE",
            "status": "ACCEPTED",
            "referee_id": referee_id,
            "reason": None
        }
```

#### 4.3.3 Round-Robin Schedule Generation

```python
from itertools import combinations

def create_schedule(player_ids: List[str]) -> List[Dict]:
    """
    Generate round-robin schedule using combinations.

    Args:
        player_ids: List of player IDs

    Returns:
        List of match dictionaries with match_id, player_A_id, player_B_id
    """
    matches = []
    round_num = 1
    match_num = 1

    # Generate all unique pairs
    for player_a, player_b in combinations(player_ids, 2):
        matches.append({
            "match_id": f"R{round_num}M{match_num}",
            "game_type": "even_odd",
            "player_A_id": player_a,
            "player_B_id": player_b
        })
        match_num += 1

    return matches
```

**Acceptance Criteria:**
- ✅ Every player plays every other player exactly once
- ✅ Total matches = N×(N-1)/2 (where N = number of players)
- ✅ No player plays themselves
- ✅ Match IDs follow pattern "R{round}M{match}"

---

## 5. HTTP Communication Patterns

### 5.1 MCP Tool Call Pattern

**Purpose:** Standardized way to call MCP tools on remote servers.

```python
import requests
from typing import Dict, Any, Optional

def call_mcp_tool(
    endpoint: str,
    method: str,
    params: Dict[str, Any],
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Send MCP tool call via HTTP POST.

    Args:
        endpoint: Full URL to MCP server (e.g., "http://localhost:8101/mcp")
        method: MCP method name (e.g., "choose_parity")
        params: Method parameters
        timeout: Request timeout in seconds

    Returns:
        Response dictionary (result or error)
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()
        return response.json()

    except requests.Timeout:
        return {
            "error": {
                "code": "E001",
                "message": "TIMEOUT_ERROR",
                "data": {"timeout": timeout}
            }
        }

    except requests.RequestException as e:
        return {
            "error": {
                "code": "E009",
                "message": "CONNECTION_ERROR",
                "data": {"exception": str(e)}
            }
        }

# Example usage
result = call_mcp_tool(
    endpoint="http://localhost:8101/mcp",
    method="choose_parity",
    params={"match_id": "R1M1", "player_id": "P01"},
    timeout=30
)

if "error" in result:
    print(f"Error: {result['error']['message']}")
else:
    choice = result.get("result", {}).get("parity_choice")
    print(f"Player chose: {choice}")
```

**Acceptance Criteria:**
- ✅ Timeout enforced at HTTP level
- ✅ Timeout error returns E001 code
- ✅ Connection error returns E009 code
- ✅ Response status checked (raise_for_status)
- ✅ Returns consistent error format

---

## 6. State Management

### 6.1 Player State Storage

**Purpose:** Players must maintain state across matches for strategy learning.

```python
from dataclasses import dataclass, field
from typing import List, Dict, Any
import json
from pathlib import Path

@dataclass
class MatchRecord:
    """Single match record."""
    match_id: str
    opponent_id: str
    my_choice: str
    opponent_choice: str
    drawn_number: int
    result: str  # "WIN", "LOSS", "DRAW"
    timestamp: str

@dataclass
class PlayerState:
    """Persistent player state."""
    player_id: str
    wins: int = 0
    losses: int = 0
    draws: int = 0
    points: int = 0
    match_history: List[MatchRecord] = field(default_factory=list)

    def record_match(self, match: MatchRecord):
        """Add match to history and update stats."""
        self.match_history.append(match)

        if match.result == "WIN":
            self.wins += 1
            self.points += 3
        elif match.result == "DRAW":
            self.draws += 1
            self.points += 1
        elif match.result == "LOSS":
            self.losses += 1

    def get_opponent_history(self, opponent_id: str) -> List[MatchRecord]:
        """Get all matches against specific opponent."""
        return [m for m in self.match_history if m.opponent_id == opponent_id]

    def save_to_file(self, filepath: str = "player_state.json"):
        """Persist state to JSON file."""
        data = {
            "player_id": self.player_id,
            "wins": self.wins,
            "losses": self.losses,
            "draws": self.draws,
            "points": self.points,
            "match_history": [
                {
                    "match_id": m.match_id,
                    "opponent_id": m.opponent_id,
                    "my_choice": m.my_choice,
                    "opponent_choice": m.opponent_choice,
                    "drawn_number": m.drawn_number,
                    "result": m.result,
                    "timestamp": m.timestamp
                }
                for m in self.match_history
            ]
        }

        Path(filepath).write_text(json.dumps(data, indent=2))

    @classmethod
    def load_from_file(cls, filepath: str = "player_state.json") -> "PlayerState":
        """Load state from JSON file."""
        if not Path(filepath).exists():
            return cls(player_id="UNKNOWN")

        data = json.loads(Path(filepath).read_text())

        state = cls(
            player_id=data["player_id"],
            wins=data["wins"],
            losses=data["losses"],
            draws=data["draws"],
            points=data["points"]
        )

        for m in data["match_history"]:
            state.match_history.append(MatchRecord(**m))

        return state
```

**Acceptance Criteria:**
- ✅ State persisted to file after each match
- ✅ State loaded at agent startup (if file exists)
- ✅ Opponent-specific history queryable
- ✅ Statistics updated correctly

---

## 7. Error Handling & Resilience

### 7.1 Retry Logic with Exponential Backoff

**Purpose:** Handle transient failures (network issues, temporary server unavailability).

```python
import time
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class RetryConfig:
    """Retry configuration."""
    max_retries: int = 3
    base_delay: float = 2.0  # seconds
    backoff_multiplier: float = 2.0
    retryable_errors: list = field(default_factory=lambda: ["E001", "E009"])

def call_with_retry(
    endpoint: str,
    method: str,
    params: Dict[str, Any],
    config: RetryConfig = RetryConfig()
) -> Dict[str, Any]:
    """
    Send MCP request with automatic retry logic.

    Args:
        endpoint: Target MCP server URL
        method: MCP method name
        params: Method parameters
        config: Retry configuration

    Returns:
        Response dictionary (result or error after max retries)
    """
    last_error = None

    for attempt in range(config.max_retries):
        try:
            response = requests.post(
                endpoint,
                json={
                    "jsonrpc": "2.0",
                    "method": method,
                    "params": params,
                    "id": 1
                },
                timeout=30
            )

            result = response.json()

            # Check if error is retryable
            if "error" in result:
                error_code = result["error"].get("code", "")
                if error_code not in config.retryable_errors:
                    # Non-retryable error - fail immediately
                    return result
                last_error = result
            else:
                # Success - return result
                return result

        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = {
                "error": {
                    "code": "E009",
                    "message": "CONNECTION_ERROR",
                    "data": {"exception": str(e), "attempt": attempt + 1}
                }
            }

        # Wait before retry (exponential backoff)
        if attempt < config.max_retries - 1:
            delay = config.base_delay * (config.backoff_multiplier ** attempt)
            print(f"Retry {attempt + 1}/{config.max_retries} after {delay}s")
            time.sleep(delay)

    # Max retries exhausted - return last error
    return last_error or {"error": {"code": "E099", "message": "MAX_RETRIES_EXCEEDED"}}
```

**Acceptance Criteria:**
- ✅ Max 3 retry attempts
- ✅ Exponential backoff: 2s, 4s, 8s
- ✅ Only retries E001 (timeout) and E009 (connection)
- ✅ Non-retryable errors fail immediately
- ✅ Returns last error after max retries

---

### 7.2 Circuit Breaker Pattern

**Purpose:** Prevent cascading failures by stopping requests to repeatedly failing services.

```python
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "CLOSED"      # Normal operation
    OPEN = "OPEN"          # Blocking requests (failure threshold exceeded)
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker to prevent repeated calls to failing services.

    States:
    - CLOSED: Normal operation, requests allowed
    - OPEN: Too many failures, blocking all requests
    - HALF_OPEN: Testing recovery, allow one request
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        reset_timeout: int = 60,
        name: str = "default"
    ):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.name = name

        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = CircuitState.CLOSED

    def can_execute(self) -> bool:
        """Check if request is allowed."""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # Check if enough time has passed to try again
            if self.last_failure_time:
                elapsed = datetime.now() - self.last_failure_time
                if elapsed > timedelta(seconds=self.reset_timeout):
                    print(f"[{self.name}] OPEN → HALF_OPEN (timeout expired)")
                    self.state = CircuitState.HALF_OPEN
                    return True
            return False

        # HALF_OPEN: allow one test request
        return True

    def record_success(self):
        """Record successful request."""
        if self.state == CircuitState.HALF_OPEN:
            print(f"[{self.name}] HALF_OPEN → CLOSED (recovery confirmed)")

        self.failures = 0
        self.state = CircuitState.CLOSED

    def record_failure(self):
        """Record failed request."""
        self.failures += 1
        self.last_failure_time = datetime.now()

        if self.failures >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                print(f"[{self.name}] CLOSED → OPEN (threshold {self.failure_threshold} exceeded)")
            self.state = CircuitState.OPEN

# Usage example
breaker = CircuitBreaker(failure_threshold=5, reset_timeout=60, name="Player:P01")

def safe_call(endpoint, method, params):
    """Call with circuit breaker protection."""
    if not breaker.can_execute():
        return {"error": "Circuit breaker OPEN - service unavailable"}

    result = call_mcp_tool(endpoint, method, params)

    if "error" in result:
        breaker.record_failure()
    else:
        breaker.record_success()

    return result
```

**Acceptance Criteria:**
- ✅ State transitions: CLOSED → OPEN → HALF_OPEN → CLOSED
- ✅ Blocks requests in OPEN state
- ✅ Allows test request in HALF_OPEN state
- ✅ Resets after timeout period (60s default)
- ✅ Tracks failures per endpoint

---

## 8. Structured Logging

### 8.1 JSON Logging Format

**Purpose:** Enable log aggregation, filtering, and analysis across distributed system.

**Required Log Fields:**

| Field | Type | Mandatory | Description |
|-------|------|-----------|-------------|
| timestamp | ISO8601 | Yes | Event time in UTC |
| level | string | Yes | DEBUG/INFO/WARN/ERROR |
| agent_id | string | Yes | Agent identifier (e.g., "player:P01") |
| message | string | Yes | Human-readable message |
| message_type | string | No | Protocol message type |
| conversation_id | string | No | Conversation/match ID |
| data | object | No | Additional context |

### 8.2 Structured Logger Implementation

```python
import json
import sys
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from enum import Enum

class LogLevel(Enum):
    """Log severity levels."""
    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3

class StructuredLogger:
    """
    JSON structured logger for distributed systems.

    Usage:
        logger = StructuredLogger("player:P01", min_level="INFO")
        logger.info("Match started",
                   message_type="GAME_INVITATION",
                   conversation_id="conv123",
                   data={"opponent": "P02"})
    """

    def __init__(self, agent_id: str, min_level: str = "INFO"):
        self.agent_id = agent_id
        self.min_level = LogLevel[min_level]

    def log(
        self,
        level: str,
        message: str,
        message_type: Optional[str] = None,
        conversation_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None
    ):
        """
        Log a structured message.

        Args:
            level: Log level (DEBUG/INFO/WARN/ERROR)
            message: Human-readable message
            message_type: Protocol message type (optional)
            conversation_id: Conversation/match ID (optional)
            data: Additional context (optional)
        """
        level_enum = LogLevel[level]

        # Check if level meets minimum
        if level_enum.value < self.min_level.value:
            return

        # Build log entry
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "agent_id": self.agent_id,
            "message": message
        }

        # Add optional fields
        if message_type:
            log_entry["message_type"] = message_type
        if conversation_id:
            log_entry["conversation_id"] = conversation_id
        if data:
            log_entry["data"] = data

        # Output to stderr (convention for logs)
        print(json.dumps(log_entry), file=sys.stderr)

    def debug(self, message: str, **kwargs):
        """Log DEBUG level message."""
        self.log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log INFO level message."""
        self.log("INFO", message, **kwargs)

    def warn(self, message: str, **kwargs):
        """Log WARN level message."""
        self.log("WARN", message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log ERROR level message."""
        self.log("ERROR", message, **kwargs)

# Usage example
logger = StructuredLogger("player:P01", min_level="INFO")

logger.info(
    "Received game invitation",
    message_type="GAME_INVITATION",
    conversation_id="convr1m1001",
    data={"match_id": "R1M1", "opponent": "P02"}
)

logger.error(
    "Failed to connect to referee",
    data={"endpoint": "http://localhost:8001", "error": "timeout"}
)
```

**Example Log Output:**
```json
{
  "timestamp": "2025-01-15T10:30:00.123456+00:00",
  "level": "INFO",
  "agent_id": "player:P01",
  "message": "Received game invitation",
  "message_type": "GAME_INVITATION",
  "conversation_id": "convr1m1001",
  "data": {
    "match_id": "R1M1",
    "opponent": "P02"
  }
}
```

**Acceptance Criteria:**
- ✅ All logs in JSON format
- ✅ Timestamp in ISO 8601 UTC format
- ✅ agent_id identifies log source
- ✅ Logs written to stderr (not stdout)
- ✅ Filterable by level, message_type, conversation_id

---

## 9. Authentication & Security

### 9.1 Token Lifecycle

**Flow:**
1. **Registration**: Agent registers → receives `auth_token`
2. **Storage**: Agent stores token securely (environment variable or config file)
3. **Usage**: Agent includes `auth_token` in all subsequent messages
4. **Validation**: Receiver validates token before processing request
5. **Expiration**: Token valid for league duration (no rotation in v2.1)

### 9.2 Receiving and Storing Token

```python
import os
import requests
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class AgentCredentials:
    """Agent authentication credentials."""
    agent_id: str
    auth_token: str
    league_id: str

    def save_to_env_file(self, filepath: str = ".env"):
        """Save credentials to .env file."""
        Path(filepath).write_text(
            f"AGENT_ID={self.agent_id}\n"
            f"AUTH_TOKEN={self.auth_token}\n"
            f"LEAGUE_ID={self.league_id}\n"
        )

    @classmethod
    def load_from_env(cls) -> Optional["AgentCredentials"]:
        """Load credentials from environment variables."""
        agent_id = os.getenv("AGENT_ID")
        auth_token = os.getenv("AUTH_TOKEN")
        league_id = os.getenv("LEAGUE_ID")

        if all([agent_id, auth_token, league_id]):
            return cls(agent_id, auth_token, league_id)
        return None

def register_player(
    league_endpoint: str,
    display_name: str,
    port: int
) -> Optional[AgentCredentials]:
    """
    Register player and receive auth token.

    Returns:
        AgentCredentials if successful, None otherwise
    """
    payload = {
        "jsonrpc": "2.0",
        "method": "register_player",
        "params": {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_REQUEST",
            "sender": f"player:{display_name}",
            "player_meta": {
                "display_name": display_name,
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": f"http://localhost:{port}/mcp"
            }
        },
        "id": 1
    }

    try:
        response = requests.post(league_endpoint, json=payload, timeout=10)
        result = response.json().get("result", {})

        if result.get("status") == "ACCEPTED":
            creds = AgentCredentials(
                agent_id=result["player_id"],
                auth_token=result["auth_token"],
                league_id=result["league_id"]
            )

            # Save to .env file
            creds.save_to_env_file()

            print(f"✓ Registered as {creds.agent_id}")
            return creds
        else:
            print(f"✗ Registration rejected: {result.get('reason')}")
            return None

    except Exception as e:
        print(f"✗ Registration failed: {e}")
        return None
```

### 9.3 Using Token in Requests

```python
class AuthenticatedMCPClient:
    """MCP client with automatic token injection."""

    def __init__(self, credentials: AgentCredentials):
        self.creds = credentials

    def call_tool(
        self,
        endpoint: str,
        method: str,
        message_type: str,
        params: dict
    ) -> dict:
        """
        Send authenticated MCP request.

        Automatically includes:
        - protocol version
        - auth_token
        - sender identification
        - league_id
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": {
                "protocol": "league.v2",
                "message_type": message_type,
                "sender": f"player:{self.creds.agent_id}",
                "auth_token": self.creds.auth_token,
                "league_id": self.creds.league_id,
                **params  # Merge additional params
            },
            "id": 1
        }

        response = requests.post(endpoint, json=payload, timeout=30)
        return response.json()

# Usage
creds = AgentCredentials.load_from_env()
client = AuthenticatedMCPClient(creds)

result = client.call_tool(
    endpoint="http://localhost:8001/mcp",
    method="choose_parity",
    message_type="CHOOSE_PARITY_RESPONSE",
    params={"match_id": "R1M1", "parity_choice": "even"}
)
```

### 9.4 Handling Authentication Errors

```python
def handle_auth_error(response: dict) -> bool:
    """
    Check for authentication errors and handle appropriately.

    Returns:
        True if no auth error, False if auth error detected
    """
    error = response.get("error", {})
    error_code = error.get("error_code", "")

    if error_code == "E011":  # AUTH_TOKEN_MISSING
        print("ERROR: auth_token is required but not provided")
        print("ACTION: Include auth_token in message envelope")
        return False

    elif error_code == "E012":  # AUTH_TOKEN_INVALID
        print("ERROR: auth_token is invalid or expired")
        print("ACTION: Re-register with League Manager to get new token")
        return False

    elif error_code == "E013":  # AGENT_NOT_REGISTERED
        print("ERROR: Agent must register before sending messages")
        print("ACTION: Call register_player or register_referee first")
        return False

    return True  # No auth error
```

**Acceptance Criteria:**
- ✅ Token received during registration
- ✅ Token stored securely (env file or config)
- ✅ Token included in all post-registration messages
- ✅ Auth errors handled with clear error messages
- ✅ Token never logged or printed (security)

---

## 10. Local Testing & Deployment

### 10.1 Component Startup Order

**CRITICAL:** Components must start in specific order to avoid connection failures.

**Correct Startup Sequence:**

```bash
# Step 1: Start League Manager (FIRST)
# Terminal 1
cd league_manager
python main.py
# Wait for: "Uvicorn running on http://0.0.0.0:8000"

# Step 2: Start Referee(s) (SECOND)
# Terminal 2
cd referee
python main.py --port 8001
# Wait for: "✓ Registered as REF01"

# Step 3: Start Player Agents (LAST)
# Terminals 3-6
cd player
python main.py --port 8101 --name "Agent Alpha"
python main.py --port 8102 --name "Agent Beta"
python main.py --port 8103 --name "Agent Gamma"
python main.py --port 8104 --name "Agent Delta"
# Wait for: "✓ Registered as P01, P02, P03, P04"

# Step 4: Start Tournament (via Orchestrator)
python orchestrator.py start-league
```

**Why This Order Matters:**
- League Manager must be running before others can register
- Referees register immediately at startup → League Manager must exist
- Players register immediately at startup → League Manager must exist
- Tournament can't start until all components registered

---

### 10.2 Health Check Script

```python
import requests
from typing import List, Tuple

def check_server_health(port: int, name: str) -> Tuple[bool, str]:
    """
    Check if MCP server is healthy.

    Returns:
        (is_healthy, status_message)
    """
    try:
        # Try health endpoint first
        response = requests.get(
            f"http://localhost:{port}/health",
            timeout=2
        )
        if response.status_code == 200:
            return True, f"✓ {name} (port {port}): Healthy"
    except:
        pass

    try:
        # Fallback: try MCP ping
        response = requests.post(
            f"http://localhost:{port}/mcp",
            json={"jsonrpc": "2.0", "method": "ping", "id": 1},
            timeout=2
        )
        if response.status_code == 200:
            return True, f"✓ {name} (port {port}): Responding"
    except:
        pass

    return False, f"✗ {name} (port {port}): FAILED"

def check_all_components():
    """Check health of all league components."""
    components = [
        (8000, "League Manager"),
        (8001, "Referee 1"),
        (8101, "Player 1 (Agent Alpha)"),
        (8102, "Player 2 (Agent Beta)"),
        (8103, "Player 3 (Agent Gamma)"),
        (8104, "Player 4 (Agent Delta)")
    ]

    print("=== League Component Health Check ===\n")

    all_healthy = True
    for port, name in components:
        is_healthy, message = check_server_health(port, name)
        print(message)
        if not is_healthy:
            all_healthy = False

    print("\n" + ("="*40))
    if all_healthy:
        print("✓ All components healthy - ready for tournament")
    else:
        print("✗ Some components failed - check logs")

    return all_healthy

if __name__ == "__main__":
    check_all_components()
```

**Usage:**
```bash
python check_health.py
```

**Expected Output:**
```
=== League Component Health Check ===

✓ League Manager (port 8000): Healthy
✓ Referee 1 (port 8001): Healthy
✓ Player 1 (Agent Alpha) (port 8101): Healthy
✓ Player 2 (Agent Beta) (port 8102): Healthy
✓ Player 3 (Agent Gamma) (port 8103): Healthy
✓ Player 4 (Agent Delta) (port 8104): Healthy

========================================
✓ All components healthy - ready for tournament
```

---

### 10.3 Local Testing Best Practices

**1. Test Registration First:**
```bash
# Test League Manager registration endpoint
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "register_player",
    "params": {
      "player_meta": {
        "display_name": "Test Player",
        "version": "1.0.0",
        "game_types": ["even_odd"],
        "contact_endpoint": "http://localhost:8101/mcp"
      }
    },
    "id": 1
  }'
```

**2. Test Player Tools:**
```bash
# Test choose_parity tool
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "choose_parity",
    "params": {
      "match_id": "R1M1",
      "player_id": "P01"
    },
    "id": 1
  }'
```

**3. Run Mini-Tournament:**
```python
# test_mini_tournament.py
def run_mini_tournament():
    """Run a 2-player, 1-match tournament for testing."""

    # 1. Register 2 players
    # 2. Create 1 match
    # 3. Run match
    # 4. Verify result reported
    # 5. Check standings updated

    print("Mini-tournament test: PASSED")
```

**Acceptance Criteria:**
- ✅ All components start in correct order
- ✅ Health checks pass for all components
- ✅ Registration succeeds for all agents
- ✅ At least one complete match executes successfully
- ✅ Logs written to files for debugging

---

## 11. Implementation Best Practices

### 11.1 Development Workflow

**Recommended Order:**

1. **Start Simple - Random Strategy**
   - Implement basic player agent with random choice
   - Focus on getting protocol communication working
   - Test registration and match flow

2. **Test Locally**
   - Run mini-tournaments with yourself (2-4 players)
   - Verify all message types work
   - Check logs for errors

3. **Add State Management**
   - Store match history
   - Track opponent patterns
   - Persist state to file

4. **Implement Adaptive Strategy**
   - Analyze opponent history
   - Detect patterns statistically
   - Exploit non-random opponents

5. **Add LLM Strategy (Optional)**
   - Integrate Claude API
   - Implement fallback to adaptive strategy
   - Handle timeouts carefully

---

### 11.2 Code Quality Checklist

**Before Submitting Agent:**

- [ ] All 3 required tools implemented (player)
- [ ] Responds within timeout limits (5s, 30s)
- [ ] Choice validation: only "even" or "odd" (case-sensitive)
- [ ] Error handling: try/except around all network calls
- [ ] Logging: structured JSON logs with conversation_id
- [ ] State persistence: saves history to file
- [ ] Auth token: stored securely, included in all messages
- [ ] Health endpoint: returns 200 OK
- [ ] Tested locally: completes at least 5 matches successfully
- [ ] No hardcoded ports: accepts port as command-line arg

---

### 11.3 Common Pitfalls to Avoid

**❌ DON'T:**
- Use `random` module for number drawing (use `secrets`)
- Hardcode opponent strategies (must work against any agent)
- Block on long-running operations (use async or threads)
- Log auth tokens (security risk)
- Ignore errors (must handle all error cases)
- Use sequential port numbers (allows port sniffing)

**✅ DO:**
- Use `secrets` module for randomness
- Implement generic strategy (opponent-agnostic)
- Use async handlers in FastAPI
- Redact sensitive data in logs
- Handle errors gracefully with retries
- Randomize or configure ports

---

## 12. User Stories

### US-1: Implement Basic Player Agent
> **As a** student developer
> **I want to** use a FastAPI template to implement my player agent
> **So that** I can focus on strategy rather than boilerplate
>
> **Acceptance Criteria:**
> - ✅ Template includes all 3 required tools
> - ✅ Server starts on configurable port
> - ✅ Health endpoint responds correctly
> - ✅ Logs in structured JSON format

### US-2: Register with League Manager
> **As a** player agent
> **I want to** automatically register at startup
> **So that** I can participate in tournaments without manual intervention
>
> **Acceptance Criteria:**
> - ✅ Registration attempted at startup
> - ✅ Auth token stored securely
> - ✅ Registration errors logged clearly
> - ✅ Retry on transient failures

### US-3: Handle Network Failures Gracefully
> **As a** referee
> **I want to** retry failed player requests with exponential backoff
> **So that** transient network issues don't cause match forfeits
>
> **Acceptance Criteria:**
> - ✅ Max 3 retry attempts
> - ✅ Exponential backoff (2s, 4s, 8s)
> - ✅ Only retries retryable errors
> - ✅ Technical loss after max retries

### US-4: Debug Distributed System Issues
> **As a** system administrator
> **I want to** structured JSON logs with conversation IDs
> **So that** I can trace requests across multiple components
>
> **Acceptance Criteria:**
> - ✅ All logs in JSON format
> - ✅ conversation_id in all match-related logs
> - ✅ Logs include agent_id, timestamp, level
> - ✅ Queryable by conversation_id or agent_id

### US-5: Test Agent Locally
> **As a** student developer
> **I want to** health check scripts and mini-tournament tests
> **So that** I can verify my agent works before submitting
>
> **Acceptance Criteria:**
> - ✅ Health check script verifies all components running
> - ✅ Mini-tournament test runs 1 complete match
> - ✅ Clear error messages if components missing
> - ✅ Exit code indicates success/failure

---

## 13. Acceptance Criteria

### 13.1 MCP Server Implementation
- ✅ FastAPI server runs on configurable port
- ✅ `/mcp` endpoint handles JSON-RPC 2.0 requests
- ✅ `/health` endpoint returns status
- ✅ Unknown methods return JSON-RPC error -32601
- ✅ Exceptions caught and returned as JSON-RPC error -32603

### 13.2 Player Agent
- ✅ Implements handle_game_invitation (responds < 5s)
- ✅ Implements choose_parity (responds < 30s, returns "even" or "odd")
- ✅ Implements notify_match_result (stores history)
- ✅ State persisted to file after each match
- ✅ Registers with League Manager at startup

### 13.3 Referee
- ✅ Registers with League Manager at startup
- ✅ Uses `secrets` module for random number generation
- ✅ Winner determination logic follows Even/Odd rules
- ✅ Reports results to League Manager
- ✅ Handles player timeouts with retry logic

### 13.4 League Manager
- ✅ Registers referees (assigns referee_id)
- ✅ Registers players (assigns player_id, auth_token)
- ✅ Generates round-robin schedule correctly
- ✅ Updates standings after each match
- ✅ Broadcasts standings to all players

### 13.5 Error Handling
- ✅ Retry logic: max 3 attempts, exponential backoff
- ✅ Circuit breaker: opens after 5 failures, resets after 60s
- ✅ Timeouts enforced at HTTP request level
- ✅ All errors logged with structured format

### 13.6 Logging
- ✅ All logs in JSON format
- ✅ Mandatory fields: timestamp, level, agent_id, message
- ✅ Logs written to stderr
- ✅ conversation_id included in match-related logs

### 13.7 Authentication
- ✅ Auth token received during registration
- ✅ Token stored securely (not in code)
- ✅ Token included in all post-registration messages
- ✅ Auth errors handled with clear messages

### 13.8 Local Testing
- ✅ Components start in correct order
- ✅ Health checks pass
- ✅ Mini-tournament completes successfully
- ✅ Logs written to files

---

## 14. Success Metrics

### 14.1 Development Productivity
- **Time to First Working Agent:** < 2 hours (using templates)
- **Registration Success Rate:** > 95% on first attempt
- **Local Test Success Rate:** > 90% pass mini-tournament
- **Code Reuse:** > 80% of students use provided templates

### 14.2 System Reliability
- **Match Completion Rate:** > 98% (with retries)
- **Retry Success Rate:** > 80% of retryable errors succeed
- **Circuit Breaker Activations:** < 5% of endpoints enter OPEN state
- **Timeout Rate:** < 5% of requests timeout

### 14.3 Debuggability
- **Issue Resolution Time:** < 30 minutes average (using logs)
- **Log Completeness:** 100% of matches have complete log trace
- **Conversation Traceability:** 100% of matches have conversation_id
- **Error Clarity:** > 90% of errors have actionable error messages

### 14.4 Student Success
- **Implementation Success:** > 95% of students complete working agent
- **Strategy Diversity:** > 3 distinct strategy types observed
- **Advanced Features:** > 50% implement adaptive strategy
- **LLM Integration:** > 20% implement LLM-based strategy

---

**Document Status:** DRAFT - Pending Review
**Next Review Date:** 2025-12-27
**Approvers:** Technical Lead, Course Instructor, DevOps Lead

**CRITICAL NOTE:** This implementation guide provides production-grade patterns. Students are encouraged to use these templates as starting points for their agents.
