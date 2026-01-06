# Developer Implementation Guide
# Quick Reference for Building League Agents

**Document Version:** 1.0
**Date:** 2025-12-20
**Audience:** Backend Developers
**Prerequisites:** `implementation-architecture-prd.md` (detailed specifications)

---

## Quick Start Checklist

### Phase 1: Setup (30 minutes)
- [ ] Clone project repository
- [ ] Install dependencies: `pip install fastapi uvicorn pydantic requests python-dotenv`
- [ ] Review protocol messages: `docs/requirements/game-protocol-messages-prd.md`
- [ ] Copy player agent template (see Section 2)
- [ ] Test server startup: `python player.py --port 8101`

### Phase 2: Core Implementation (2 hours)
- [ ] Implement 3 required tools: `handle_game_invitation`, `choose_parity`, `notify_match_result`
- [ ] Add structured logging with JSON format
- [ ] Implement token storage and authentication
- [ ] Add state persistence (save match history to file)
- [ ] Test locally with health check script

### Phase 3: Strategy (2-4 hours)
- [ ] Start with random strategy (baseline)
- [ ] Implement opponent history tracking
- [ ] Add pattern detection (adaptive strategy)
- [ ] (Optional) Integrate LLM for strategic reasoning

### Phase 4: Testing & Deployment (1 hour)
- [ ] Run mini-tournament test (2-4 players)
- [ ] Verify all timeouts respected (5s, 30s)
- [ ] Check logs for errors
- [ ] Submit agent for tournament

**Total Time Estimate:** 5-8 hours from zero to tournament-ready agent

---

## 1. Player Agent Implementation Requirements

### 1.1 MCP Server Requirements

**Your agent MUST implement an HTTP server that:**
- ✅ Listens on a localhost port (e.g., 8101-8150)
- ✅ Accepts HTTP POST requests at the `/mcp` endpoint
- ✅ Returns responses in JSON-RPC 2.0 format
- ✅ Implements exactly 3 required tools (see below)

### 1.2 Required Tools (Mandatory)

**Tool 1: handle_game_invitation**
- **Purpose:** Receive game invitation from referee
- **Input:** `{match_id, game_type, opponent_id, role_in_match, conversation_id}`
- **Output:** `GAME_JOIN_ACK` message
- **Response Time:** Within 5 seconds (CRITICAL)
- **Failure Consequence:** Match forfeit if timeout

**Tool 2: choose_parity**
- **Purpose:** Make strategic choice ("even" or "odd")
- **Input:** `{match_id, player_id, context: {opponent_id, round_id, your_standings}}`
- **Output:** `CHOOSE_PARITY_RESPONSE` message
- **Response Time:** Within 30 seconds (CRITICAL)
- **Failure Consequence:** Match forfeit if timeout (after 3 retries)

**Tool 3: notify_match_result**
- **Purpose:** Receive match outcome and update internal state
- **Input:** `{match_id, game_result: {status, winner, choices, drawn_number}}`
- **Output:** Acknowledgment message
- **Response Time:** Within 10 seconds (recommended)
- **Failure Consequence:** Warning logged (not critical)

### 1.3 League Registration Requirements

**Your agent MUST send registration request to League Manager (port 8000) containing:**
- ✅ **Unique display name** - Your name or nickname (max 50 characters)
- ✅ **Agent version** - Semantic versioning (e.g., "1.0.0")
- ✅ **Server endpoint** - Full HTTP URL (e.g., "http://localhost:8101/mcp")
- ✅ **Supported game types** - List including "even_odd"

**Registration happens at agent startup, before tournament begins.**

### 1.4 Technical Requirements Summary

| Requirement | Specification | Mandatory |
|-------------|---------------|-----------|
| **Server Type** | HTTP server (FastAPI recommended) | Yes |
| **Endpoint Path** | `/mcp` (POST requests only) | Yes |
| **Response Format** | JSON-RPC 2.0 | Yes |
| **Port Range** | 8101-8150 (players) | Yes |
| **Required Tools** | All 3 tools implemented | Yes |
| **Response Times** | 5s (invitation), 30s (choice), 10s (result) | Yes |
| **Stability** | No crashes during tournament | Yes |
| **Error Handling** | Handle invalid inputs gracefully | Yes |

### 1.5 Response Time Requirements (CRITICAL)

**Timeout Compliance Table:**

| Message Type | Maximum Response Time | Consequence of Violation |
|--------------|----------------------|--------------------------|
| `GAME_JOIN_ACK` | **5 seconds** | Immediate match forfeit (0 points) |
| `CHOOSE_PARITY_RESPONSE` | **30 seconds** | 3 retries, then forfeit (0 points) |
| Other responses | **10 seconds** | Warning logged, may affect scoring |

**⚠️ WARNING:** Exceeding these timeouts results in automatic match loss (TECHNICAL_LOSS).

### 1.6 Stability Requirements

**Your agent MUST:**
- ✅ Operate without crashes throughout entire tournament
- ✅ Handle malformed input gracefully (return error, don't crash)
- ✅ Continue functioning even after receiving unexpected messages
- ✅ Recover from transient errors (network issues, temporary failures)
- ✅ Never stop responding mid-tournament

**Crash = Disqualification from tournament**

### 1.7 Self-Testing Checklist

**Before submission, you MUST:**
- [ ] Run local league with **4 copies of your agent** (4 different ports)
- [ ] Verify agent responds to ALL message types correctly
- [ ] Confirm all JSON structures conform to protocol specification
- [ ] Test timeout compliance (responses within time limits)
- [ ] Verify no crashes occur during complete tournament run
- [ ] Check logs for errors or warnings
- [ ] Validate choice format: only "even" or "odd" (lowercase)

### 1.8 Two-Stage Work Process

**Stage 1: Local Development**
1. Implement the agent using template (Section 2)
2. Test tools individually with curl/Postman
3. Fix bugs and validate JSON responses
4. Test registration with League Manager
5. Verify timeout compliance

**Stage 2: Private League Testing**
1. Run local League Manager on port 8000
2. Start 4 copies of your agent on ports 8101-8104
3. Execute complete tournament (all rounds)
4. Monitor logs for errors
5. Verify standings calculation
6. Improve strategy based on results
7. Repeat until stable

**Minimum Requirement:** Agent must complete at least one full 4-player tournament without crashes.

---

## 2. System Architecture Overview

```
Orchestrator (Control Script)
    ↓
League Manager :8000 ← You register here
    ↓
Referee :8001 ← Invites you to matches
    ↓
Your Player Agent :8101 ← You implement this
```

**Communication Protocol:**
- **Transport:** HTTP POST requests
- **Format:** JSON-RPC 2.0
- **Content-Type:** `application/json`
- **Authentication:** Token-based (received during registration)

**Port Assignments:**
- League Manager: `8000` (fixed)
- Referees: `8001-8010`
- Players: `8101-8150`

---

## 2. Minimal Player Agent Template

```python
# player.py - Minimal working player agent

import random
import requests
from datetime import datetime, timezone
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Player Agent")

# ============================================================================
# CONFIGURATION
# ============================================================================

PLAYER_NAME = "Agent Alpha"
PLAYER_PORT = 8101
LEAGUE_ENDPOINT = "http://localhost:8000/mcp"

# ============================================================================
# STATE STORAGE
# ============================================================================

class PlayerState:
    def __init__(self):
        self.player_id = None
        self.auth_token = None
        self.match_history = []

    def record_match(self, result):
        self.match_history.append(result)

state = PlayerState()

# ============================================================================
# MCP TOOLS (3 REQUIRED)
# ============================================================================

@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """Main MCP endpoint - routes to tool handlers."""
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
    """
    Tool 1: Accept game invitation.
    Timeout: 5 seconds
    """
    return {
        "jsonrpc": "2.0",
        "result": {
            "message_type": "GAME_JOIN_ACK",
            "match_id": params.get("match_id"),
            "player_id": state.player_id,
            "arrival_timestamp": datetime.now(timezone.utc).isoformat(),
            "accept": True  # Always accept
        },
        "id": 1
    }

def choose_parity(params: dict) -> dict:
    """
    Tool 2: Choose "even" or "odd".
    Timeout: 30 seconds
    Strategy: Random (50/50)
    """
    # TODO: Implement adaptive strategy using state.match_history
    choice = random.choice(["even", "odd"])

    return {
        "jsonrpc": "2.0",
        "result": {
            "message_type": "CHOOSE_PARITY_RESPONSE",
            "match_id": params.get("match_id"),
            "player_id": params.get("player_id"),
            "parity_choice": choice  # MUST be "even" or "odd" (lowercase)
        },
        "id": 1
    }

def handle_result(params: dict) -> dict:
    """
    Tool 3: Receive match result.
    Timeout: 5 seconds (best-effort)
    """
    state.record_match(params)
    print(f"[RESULT] Total matches: {len(state.match_history)}")

    return {
        "jsonrpc": "2.0",
        "result": {"status": "ok"},
        "id": 1
    }

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health endpoint for monitoring."""
    return {"status": "healthy", "player_id": state.player_id}

# ============================================================================
# REGISTRATION
# ============================================================================

def register_with_league():
    """Register with League Manager at startup."""
    payload = {
        "jsonrpc": "2.0",
        "method": "register_player",
        "params": {
            "player_meta": {
                "display_name": PLAYER_NAME,
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": f"http://localhost:{PLAYER_PORT}/mcp"
            }
        },
        "id": 1
    }

    try:
        response = requests.post(LEAGUE_ENDPOINT, json=payload, timeout=10)
        result = response.json().get("result", {})

        if result.get("status") == "ACCEPTED":
            state.player_id = result["player_id"]
            state.auth_token = result["auth_token"]
            print(f"✓ Registered as {state.player_id}")
        else:
            print(f"✗ Registration rejected: {result.get('reason')}")

    except Exception as e:
        print(f"✗ Registration failed: {e}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    # Register before starting server
    register_with_league()

    # Start FastAPI server
    uvicorn.run(app, host="0.0.0.0", port=PLAYER_PORT)
```

**Usage:**
```bash
python player.py
```

**Expected Output:**
```
✓ Registered as P01
INFO:     Uvicorn running on http://0.0.0.0:8101 (Press CTRL+C to quit)
```

---

## 3. Critical Implementation Requirements

### 3.1 Required Tools (Mandatory)

**You MUST implement exactly these 3 tools:**

| Tool Name | Input | Output | Timeout | Failure Consequence |
|-----------|-------|--------|---------|---------------------|
| `handle_game_invitation` | `{match_id, opponent_id, ...}` | `{accept: true/false}` | 5s | Match forfeit (0 points) |
| `choose_parity` | `{match_id, player_id, context}` | `{parity_choice: "even"\|"odd"}` | 30s | Match forfeit (0 points) |
| `notify_match_result` | `{match_id, game_result}` | `{status: "ok"}` | 5s | Warning only (not critical) |

### 3.2 Choice Validation (Critical)

**VALID choices:**
```python
"even"  # ✅ Lowercase string
"odd"   # ✅ Lowercase string
```

**INVALID choices (will cause error E004):**
```python
"Even"  # ❌ Wrong case
"EVEN"  # ❌ Wrong case
"e"     # ❌ Abbreviation
0       # ❌ Integer (must be string)
True    # ❌ Boolean (must be string)
null    # ❌ Null (must be present)
```

**Validation code:**
```python
def validate_choice(choice):
    if choice not in ["even", "odd"]:
        raise ValueError(f"Invalid choice: {choice}. Must be 'even' or 'odd'")
    return choice
```

### 3.3 Timeout Compliance

**Your agent MUST respond within these limits:**

| Message Type | Timeout | What Happens on Timeout |
|--------------|---------|-------------------------|
| Registration | 10s | Registration rejected |
| Game Invitation | 5s | Match forfeit (TECHNICAL_LOSS) |
| Choose Parity | 30s | Match forfeit after 3 retries |
| Match Result | 5s | Warning logged (not critical) |

**How to ensure compliance:**
- Use async handlers in FastAPI (prevents blocking)
- Keep logic simple in tool handlers
- Move heavy computation to background threads
- If using LLM API: set timeout to 25s max (5s buffer)

---

## 4. State Management

### 4.1 What to Store

```python
class PlayerState:
    def __init__(self):
        self.player_id = None      # Your ID (e.g., "P01")
        self.auth_token = None     # Authentication token
        self.match_history = []    # List of all match results

        # Statistics
        self.wins = 0
        self.losses = 0
        self.draws = 0
        self.points = 0

    def record_match(self, result):
        """Store match and update stats."""
        self.match_history.append(result)

        status = result.get("game_result", {}).get("status")
        winner = result.get("game_result", {}).get("winner_player_id")

        if status == "WIN" and winner == self.player_id:
            self.wins += 1
            self.points += 3
        elif status == "WIN":
            self.losses += 1
        elif status == "DRAW":
            self.draws += 1
            self.points += 1

    def get_opponent_history(self, opponent_id):
        """Get all matches against specific opponent."""
        return [
            m for m in self.match_history
            if m.get("context", {}).get("opponent_id") == opponent_id
        ]
```

### 4.2 Persistence (Save to File)

```python
import json
from pathlib import Path

def save_state(state, filename="player_state.json"):
    """Save state to JSON file."""
    data = {
        "player_id": state.player_id,
        "wins": state.wins,
        "losses": state.losses,
        "draws": state.draws,
        "points": state.points,
        "match_history": state.match_history
    }
    Path(filename).write_text(json.dumps(data, indent=2))

def load_state(filename="player_state.json"):
    """Load state from JSON file."""
    if not Path(filename).exists():
        return PlayerState()

    data = json.loads(Path(filename).read_text())
    state = PlayerState()
    state.player_id = data["player_id"]
    state.wins = data["wins"]
    state.losses = data["losses"]
    state.draws = data["draws"]
    state.points = data["points"]
    state.match_history = data["match_history"]

    return state
```

**Call after each match:**
```python
def handle_result(params):
    state.record_match(params)
    save_state(state)  # ← Persist to file
    return {"status": "ok"}
```

---

## 5. Strategy Implementation

### 5.1 Random Strategy (Baseline)

```python
import random

def choose_parity_random(params):
    """Random 50/50 strategy - baseline."""
    choice = random.choice(["even", "odd"])
    return {"parity_choice": choice}
```

**Expected Win Rate:** 50% (against any opponent)

---

### 5.2 Adaptive Strategy (Pattern Detection)

```python
from collections import Counter

def choose_parity_adaptive(params, state):
    """Adaptive strategy - detect and exploit patterns."""
    opponent_id = params.get("context", {}).get("opponent_id")

    # Get history against this opponent
    opp_matches = state.get_opponent_history(opponent_id)

    # Need at least 5 matches for pattern detection
    if len(opp_matches) < 5:
        return random.choice(["even", "odd"])  # Fallback to random

    # Analyze opponent's choices
    opponent_choices = [
        m.get("game_result", {}).get("choices", {}).get(opponent_id)
        for m in opp_matches
    ]

    # Count frequency
    counts = Counter(opponent_choices)
    even_count = counts.get("even", 0)
    odd_count = counts.get("odd", 0)

    # If opponent has strong bias (>65%), exploit it
    total = even_count + odd_count
    if total > 0:
        even_pct = even_count / total
        if even_pct > 0.65:
            return "even"  # Opponent favors even → we also choose even
        elif even_pct < 0.35:
            return "odd"   # Opponent favors odd → we also choose odd

    # No clear pattern - random
    return random.choice(["even", "odd"])
```

**Expected Win Rate:** > 50% (if opponent has patterns)

---

### 5.3 LLM Strategy (Optional)

```python
import anthropic
import os

def choose_parity_llm(params, state):
    """LLM-enhanced strategy using Claude API."""
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

        opponent_id = params.get("context", {}).get("opponent_id")
        opp_history = state.get_opponent_history(opponent_id)

        prompt = f"""
You are playing an Even/Odd game. Choose "even" or "odd".

Rules:
- You and opponent choose simultaneously
- Referee draws random number 1-10
- If number is even, player who chose "even" wins
- If number is odd, player who chose "odd" wins

Opponent History ({opponent_id}):
{format_history(opp_history)}

Respond with ONLY the word "even" or "odd" (lowercase).
"""

        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
            timeout=25.0  # CRITICAL: Leave 5s buffer
        )

        choice = response.content[0].text.strip().lower()

        # Validate
        if choice not in ["even", "odd"]:
            return random.choice(["even", "odd"])  # Fallback

        return choice

    except Exception as e:
        print(f"LLM error: {e}")
        return random.choice(["even", "odd"])  # Fallback
```

**CRITICAL:** Always have fallback to random/adaptive if LLM fails or times out!

---

## 6. Error Handling Patterns

### 6.1 HTTP Request with Timeout

```python
import requests

def call_mcp_tool(endpoint, method, params, timeout=30):
    """Send MCP request with timeout."""
    try:
        response = requests.post(
            endpoint,
            json={
                "jsonrpc": "2.0",
                "method": method,
                "params": params,
                "id": 1
            },
            timeout=timeout
        )
        return response.json()

    except requests.Timeout:
        return {"error": {"code": "E001", "message": "TIMEOUT_ERROR"}}

    except requests.RequestException as e:
        return {"error": {"code": "E009", "message": "CONNECTION_ERROR"}}
```

### 6.2 Retry Logic (3 attempts)

```python
import time

def call_with_retry(endpoint, method, params, max_retries=3):
    """Call with automatic retry on timeout/connection errors."""
    for attempt in range(max_retries):
        result = call_mcp_tool(endpoint, method, params)

        # Success
        if "error" not in result:
            return result

        # Check if retryable
        error_code = result.get("error", {}).get("code")
        if error_code not in ["E001", "E009"]:
            return result  # Non-retryable error

        # Wait before retry
        if attempt < max_retries - 1:
            delay = 2 * (2 ** attempt)  # 2s, 4s, 8s
            time.sleep(delay)

    return result  # Return last error
```

---

## 7. Structured Logging

### 7.1 JSON Logger

```python
import json
import sys
from datetime import datetime, timezone

def log_json(level, message, **kwargs):
    """Log in structured JSON format."""
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "agent_id": state.player_id or "unknown",
        "message": message,
        **kwargs  # Add message_type, conversation_id, data, etc.
    }
    print(json.dumps(log_entry), file=sys.stderr)

# Usage
log_json("INFO", "Received game invitation",
         message_type="GAME_INVITATION",
         conversation_id="convr1m1001",
         data={"match_id": "R1M1", "opponent": "P02"})
```

**Output:**
```json
{
  "timestamp": "2025-01-15T10:30:00.123+00:00",
  "level": "INFO",
  "agent_id": "P01",
  "message": "Received game invitation",
  "message_type": "GAME_INVITATION",
  "conversation_id": "convr1m1001",
  "data": {"match_id": "R1M1", "opponent": "P02"}
}
```

---

## 8. Local Testing

### 8.1 Startup Order (CRITICAL)

```bash
# Terminal 1: League Manager (START FIRST)
cd league_manager
python main.py

# Terminal 2: Referee (START SECOND)
cd referee
python main.py --port 8001

# Terminals 3-6: Players (START LAST)
cd player
python main.py --port 8101 --name "Agent Alpha"
python main.py --port 8102 --name "Agent Beta"
python main.py --port 8103 --name "Agent Gamma"
python main.py --port 8104 --name "Agent Delta"
```

### 8.2 Health Check Script

```python
# check_health.py
import requests

def check(port, name):
    try:
        r = requests.get(f"http://localhost:{port}/health", timeout=2)
        print(f"✓ {name} (port {port}): {r.json()}")
    except:
        print(f"✗ {name} (port {port}): FAILED")

check(8000, "League Manager")
check(8001, "Referee")
check(8101, "Player 1")
check(8102, "Player 2")
```

**Run:**
```bash
python check_health.py
```

---

## 9. Common Pitfalls & Solutions

| Problem | Cause | Solution |
|---------|-------|----------|
| "Method not found" error | Tool not registered | Check method name matches exactly |
| Timeout forfeit | Response > 30s | Use async handlers, optimize strategy |
| Invalid choice error (E004) | Wrong case or type | Use `"even"` or `"odd"` (lowercase string) |
| Registration rejected | League already started | Start League Manager first, register early |
| Connection refused | Components not running | Check startup order, use health checks |
| Auth token missing (E011) | Token not included | Add auth_token to all post-registration messages |
| Match forfeit | No response sent | Ensure all tools return proper JSON-RPC response |

---

## 10. Quick Reference

### 10.1 Required Message Formats

**GAME_JOIN_ACK:**
```json
{
  "message_type": "GAME_JOIN_ACK",
  "match_id": "R1M1",
  "player_id": "P01",
  "arrival_timestamp": "2025-01-15T10:30:00Z",
  "accept": true
}
```

**CHOOSE_PARITY_RESPONSE:**
```json
{
  "message_type": "CHOOSE_PARITY_RESPONSE",
  "match_id": "R1M1",
  "player_id": "P01",
  "parity_choice": "even"
}
```

### 10.2 Timeout Limits

| Message | Timeout | Retries |
|---------|---------|---------|
| Registration | 10s | No |
| Game Invitation | 5s | No |
| Choose Parity | 30s | Yes (3x) |
| Match Result | 5s | No |

### 10.3 Scoring

| Result | Your Points | Opponent Points |
|--------|-------------|-----------------|
| Win | 3 | 0 |
| Draw | 1 | 1 |
| Loss | 0 | 3 |
| Technical Loss (timeout) | 0 | 3 |

---

## 11. Comprehensive Testing Guide

### 11.1 Stage 1: Local Development Testing

#### 11.1.1 Test Individual Tools with curl

**Test 1: Server Startup**
```bash
# Start your agent
python player.py --port 8101

# Expected output:
# ✓ Registered as P01
# INFO: Uvicorn running on http://0.0.0.0:8101
```

**Test 2: Health Check**
```bash
curl http://localhost:8101/health

# Expected output:
# {"status":"healthy","player_id":"P01"}
```

**Test 3: handle_game_invitation**
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "handle_game_invitation",
    "params": {
      "match_id": "TEST_M1",
      "game_type": "even_odd",
      "opponent_id": "P02",
      "role_in_match": "PLAYER_A",
      "conversation_id": "test_conv"
    },
    "id": 1
  }'

# Expected output:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "message_type": "GAME_JOIN_ACK",
#     "match_id": "TEST_M1",
#     "player_id": "P01",
#     "accept": true,
#     "arrival_timestamp": "2025-01-15T10:30:00Z"
#   },
#   "id": 1
# }
```

**Test 4: choose_parity**
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "choose_parity",
    "params": {
      "match_id": "TEST_M1",
      "player_id": "P01",
      "context": {
        "opponent_id": "P02",
        "round_id": 1
      }
    },
    "id": 1
  }'

# Expected output:
# {
#   "jsonrpc": "2.0",
#   "result": {
#     "message_type": "CHOOSE_PARITY_RESPONSE",
#     "match_id": "TEST_M1",
#     "player_id": "P01",
#     "parity_choice": "even"  # or "odd"
#   },
#   "id": 1
# }
```

**Test 5: notify_match_result**
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "notify_match_result",
    "params": {
      "match_id": "TEST_M1",
      "game_result": {
        "status": "WIN",
        "winner_player_id": "P01",
        "drawn_number": 8,
        "choices": {
          "P01": "even",
          "P02": "odd"
        }
      }
    },
    "id": 1
  }'

# Expected output:
# {
#   "jsonrpc": "2.0",
#   "result": {"status": "ok"},
#   "id": 1
# }
```

#### 11.1.2 Validation Checklist

After running curl tests:
- [ ] All 3 tools respond without errors
- [ ] Response format is valid JSON-RPC 2.0
- [ ] `parity_choice` is exactly "even" or "odd" (lowercase)
- [ ] `accept` is boolean `true` (not string "true")
- [ ] All timestamps in ISO 8601 UTC format
- [ ] Server doesn't crash on any test

---

### 11.2 Stage 2: Private League Testing

#### 11.2.1 Setup Local Tournament Environment

**Directory Structure:**
```
your-agent/
  ├── player.py           # Your agent implementation
  ├── league_manager.py   # Provided by course (or implement from spec)
  ├── referee.py          # Provided by course (or implement from spec)
  └── run_tournament.sh   # Script to start all components
```

**Create Tournament Startup Script:**

**File: `run_tournament.sh` (Linux/Mac)**
```bash
#!/bin/bash

# Kill any existing processes on these ports
kill $(lsof -t -i:8000) 2>/dev/null
kill $(lsof -t -i:8001) 2>/dev/null
kill $(lsof -t -i:8101) 2>/dev/null
kill $(lsof -t -i:8102) 2>/dev/null
kill $(lsof -t -i:8103) 2>/dev/null
kill $(lsof -t -i:8104) 2>/dev/null

echo "Starting League Manager on port 8000..."
python league_manager.py &
LEAGUE_PID=$!
sleep 2

echo "Starting Referee on port 8001..."
python referee.py --port 8001 &
REFEREE_PID=$!
sleep 2

echo "Starting 4 Player Agents..."
python player.py --port 8101 --name "Agent-Alpha" &
P1_PID=$!
sleep 1

python player.py --port 8102 --name "Agent-Beta" &
P2_PID=$!
sleep 1

python player.py --port 8103 --name "Agent-Gamma" &
P3_PID=$!
sleep 1

python player.py --port 8104 --name "Agent-Delta" &
P4_PID=$!
sleep 2

echo "All components started!"
echo "League Manager PID: $LEAGUE_PID"
echo "Referee PID: $REFEREE_PID"
echo "Player 1 PID: $P1_PID"
echo "Player 2 PID: $P2_PID"
echo "Player 3 PID: $P3_PID"
echo "Player 4 PID: $P4_PID"

echo ""
echo "Press Ctrl+C to stop all components"

# Wait for user interrupt
wait
```

**File: `run_tournament.bat` (Windows)**
```batch
@echo off

echo Starting League Manager on port 8000...
start "League Manager" python league_manager.py
timeout /t 2

echo Starting Referee on port 8001...
start "Referee" python referee.py --port 8001
timeout /t 2

echo Starting 4 Player Agents...
start "Player 1" python player.py --port 8101 --name "Agent-Alpha"
timeout /t 1

start "Player 2" python player.py --port 8102 --name "Agent-Beta"
timeout /t 1

start "Player 3" python player.py --port 8103 --name "Agent-Gamma"
timeout /t 1

start "Player 4" python player.py --port 8104 --name "Agent-Delta"
timeout /t 2

echo All components started!
echo Check individual windows for logs
pause
```

#### 11.2.2 Run Complete Tournament

**Step 1: Start All Components**
```bash
chmod +x run_tournament.sh
./run_tournament.sh
```

**Step 2: Verify All Components Running**
```bash
# Run health check
python check_health.py
```

**Expected Output:**
```
=== League Component Health Check ===

✓ League Manager (port 8000): Healthy
✓ Referee (port 8001): Healthy
✓ Player 1 (port 8101): Healthy
✓ Player 2 (port 8102): Healthy
✓ Player 3 (port 8103): Healthy
✓ Player 4 (port 8104): Healthy

========================================
✓ All components healthy - ready for tournament
```

**Step 3: Trigger Tournament Start**
```bash
# Send start signal to League Manager
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "start_tournament",
    "params": {},
    "id": 1
  }'
```

**Step 4: Monitor Logs**
```bash
# Watch agent logs in real-time
tail -f logs/player_8101.log
```

#### 11.2.3 Tournament Progress Monitoring

**Create Monitoring Script: `monitor_tournament.py`**
```python
import requests
import time
from datetime import datetime

def get_standings():
    """Query current standings from League Manager."""
    response = requests.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "get_standings",
            "params": {},
            "id": 1
        },
        timeout=5
    )
    return response.json().get("result", {}).get("standings", [])

def display_standings(standings):
    """Display standings in table format."""
    print("\n" + "="*60)
    print(f"Tournament Standings - {datetime.now().strftime('%H:%M:%S')}")
    print("="*60)
    print(f"{'Rank':<6} {'Player':<20} {'W':<4} {'L':<4} {'D':<4} {'Pts':<6}")
    print("-"*60)

    for s in standings:
        print(f"{s['rank']:<6} {s['display_name']:<20} "
              f"{s['wins']:<4} {s['losses']:<4} {s['draws']:<4} "
              f"{s['points']:<6}")

    print("="*60 + "\n")

# Monitor tournament every 10 seconds
while True:
    try:
        standings = get_standings()
        if standings:
            display_standings(standings)
        time.sleep(10)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        break
    except Exception as e:
        print(f"Error: {e}")
        time.sleep(10)
```

**Run Monitor:**
```bash
python monitor_tournament.py
```

**Expected Output:**
```
============================================================
Tournament Standings - 15:30:45
============================================================
Rank   Player               W    L    D    Pts
------------------------------------------------------------
1      Agent-Alpha          3    0    0    9
2      Agent-Beta           2    1    0    6
3      Agent-Gamma          1    2    0    3
4      Agent-Delta          0    3    0    0
============================================================
```

#### 11.2.4 Post-Tournament Analysis

**Check Logs for Errors:**
```bash
# Count errors by type
grep "ERROR" logs/*.log | wc -l

# Find timeout errors
grep "TIMEOUT" logs/*.log

# Check for crashes
grep "Exception" logs/*.log
```

**Verify Match Completion:**
```bash
# Total matches expected for 4 players = 6 (round-robin)
# Query League Manager for match results

curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "get_match_results",
    "params": {},
    "id": 1
  }' | jq '.result.matches | length'

# Expected output: 6
```

**Strategy Performance Analysis:**
```python
# analyze_performance.py
import json
from pathlib import Path

# Load your agent's match history
state = json.loads(Path("player_state.json").read_text())

total_matches = len(state["match_history"])
wins = state["wins"]
losses = state["losses"]
draws = state["draws"]

win_rate = (wins / total_matches * 100) if total_matches > 0 else 0

print(f"Total Matches: {total_matches}")
print(f"Wins: {wins} ({win_rate:.1f}%)")
print(f"Losses: {losses}")
print(f"Draws: {draws}")
print(f"Final Points: {state['points']}")

# Analyze choice distribution
choices = [m.get("my_choice") for m in state["match_history"]]
even_count = choices.count("even")
odd_count = choices.count("odd")

print(f"\nChoice Distribution:")
print(f"Even: {even_count} ({even_count/total_matches*100:.1f}%)")
print(f"Odd: {odd_count} ({odd_count/total_matches*100:.1f}%)")
```

---

### 11.3 Common Testing Issues & Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| **Port already in use** | `Address already in use` error | Kill process: `kill $(lsof -t -i:8101)` |
| **Registration fails** | `Connection refused` error | Start League Manager first |
| **Choice rejected** | Error E004 received | Ensure choice is "even" or "odd" (lowercase) |
| **Timeout forfeit** | TECHNICAL_LOSS in results | Optimize strategy, use async handlers |
| **Agent crashes** | Process exits unexpectedly | Add try/except blocks, check logs |
| **Standings not updating** | Points don't change | Verify result reporting to League Manager |

---

### 11.4 Pre-Submission Checklist

**Run through this checklist before submitting:**

- [ ] **Startup Test**: Agent starts without errors
- [ ] **Registration Test**: Agent registers successfully with League Manager
- [ ] **Health Check**: `/health` endpoint returns 200 OK
- [ ] **Tool Tests**: All 3 tools respond correctly to curl requests
- [ ] **Timeout Compliance**: All responses within time limits (5s, 30s, 10s)
- [ ] **Choice Validation**: Only "even" or "odd" returned (lowercase)
- [ ] **4-Player Tournament**: Complete tournament with 4 agents without crashes
- [ ] **Match Completion**: All 6 matches complete (4-player round-robin)
- [ ] **Log Review**: No ERROR or EXCEPTION messages in logs
- [ ] **State Persistence**: Match history saved to file after each game
- [ ] **Strategy Verification**: Win rate > 45% (random baseline is 50%)
- [ ] **Code Review**: No hardcoded ports, tokens, or opponent strategies

**If all checkboxes are ✅ → Agent is ready for submission! 🎉**

---

## 12. Next Steps

1. **Copy template** from Section 2
2. **Test registration**: `python player.py` → should see "✓ Registered as P01"
3. **Implement strategy**: Replace random with adaptive (Section 5.2)
4. **Add persistence**: Save state after each match (Section 4.2)
5. **Test locally**: Run mini-tournament with 2-4 players
6. **Submit**: Deploy agent for actual tournament

**Estimated Time:** 5-8 hours total

---

**Questions? See:**
- `implementation-architecture-prd.md` (detailed architecture)
- `game-protocol-messages-prd.md` (all message formats)
- `even-odd-game-prd.md` (game rules and strategies)

**Good luck! 🚀**
