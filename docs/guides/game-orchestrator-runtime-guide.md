# Game Orchestrator Runtime Guide

**Document Type:** Operational Guide
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** System Administrators, DevOps, Integration Testers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [System Configuration](#2-system-configuration)
3. [Startup Order](#3-startup-order)
4. [Stage 1: Referee Registration](#4-stage-1-referee-registration)
5. [Stage 2: Player Registration](#5-stage-2-player-registration)
6. [Stage 3: Creating Game Schedule](#6-stage-3-creating-game-schedule)
7. [Stage 4: Round Announcement](#7-stage-4-round-announcement)
8. [Stage 5: Managing a Single Game](#8-stage-5-managing-a-single-game)
9. [Stage 6: Round Completion and Standings Update](#9-stage-6-round-completion-and-standings-update)
10. [Stage 7: League Completion](#10-stage-7-league-completion)
11. [Error Handling](#11-error-handling)
12. [Available Query Tools](#12-available-query-tools)
13. [Complete Flow Diagram](#13-complete-flow-diagram)
14. [Agent Roles Reference](#14-agent-roles-reference)
15. [Monitoring and Debugging](#15-monitoring-and-debugging)
16. [Troubleshooting](#16-troubleshooting)

---

## 1. Introduction

This appendix presents a practical guide for running the complete league system. We'll demonstrate how to operate all agents and manage a league with:

- **1 League Manager** (Orchestrator)
- **2 Referees** (Game Orchestrators)
- **4 Players** (Agents)

The examples are based on the **league.v2 protocol** described in the requirements documents.

### 1.1 Document Purpose

This guide provides:
- ✅ Step-by-step instructions for starting all system components
- ✅ Complete message flow examples for all stages
- ✅ Error handling scenarios
- ✅ Monitoring and debugging strategies
- ✅ Troubleshooting common issues

### 1.2 Prerequisites

Before starting, ensure:
- All agent implementations are complete and tested
- Python 3.11+ is installed
- All dependencies are installed (`pip install -r requirements.txt`)
- Ports 8000-8104 are available on localhost
- Logging infrastructure is configured

---

## 2. System Configuration

### 2.1 Ports and Terminals

Each agent in the system operates as a separate HTTP server on a dedicated port on localhost. In this example, we'll run **7 terminals**:

**Table 1: Port and Terminal Allocation**

| Terminal | Agent           | Port | Endpoint                       |
|----------|-----------------|------|--------------------------------|
| 1        | League Manager  | 8000 | http://localhost:8000/mcp      |
| 2        | Referee REF01   | 8001 | http://localhost:8001/mcp      |
| 3        | Referee REF02   | 8002 | http://localhost:8002/mcp      |
| 4        | Player P01      | 8101 | http://localhost:8101/mcp      |
| 5        | Player P02      | 8102 | http://localhost:8102/mcp      |
| 6        | Player P03      | 8103 | http://localhost:8103/mcp      |
| 7        | Player P04      | 8104 | http://localhost:8104/mcp      |

### 2.2 Orchestrator Roles

The system has two types of Orchestrators:

1. **League Manager** – Top-level league Orchestrator
   - Source of truth for standings table
   - Source of truth for game schedule
   - Source of truth for round status
   - Manages player and referee registrations

2. **Referees** – Local Orchestrators for individual games
   - Source of truth for their game state
   - Manage game flow (invitation → choices → result)
   - Report results to League Manager

### 2.3 Configuration Files

Before starting, verify these configuration files exist:

- `SHARED/config/system.json` – System-wide settings
- `SHARED/config/leagues/league_2025_even_odd.json` – League configuration
- `SHARED/config/agents/agents_config.json` – Agent metadata
- `SHARED/config/games/games_registry.json` – Game type definitions

---

## 3. Startup Order

### 3.1 Startup Order Principle

**CRITICAL:** Startup order is critical for proper system operation:

```
1. League Manager – Must start FIRST
2. Referees – Start and register with League Manager
3. Players – Start and register with League Manager
4. League Start – Only after all registrations are complete
```

**Why order matters:**
- League Manager must be listening before any registrations
- Referees must be registered before league can create schedule
- Players must be registered before round announcements
- Premature league start will cause registration failures

### 3.2 Terminal 1 – League Manager

**Starting League Manager:**

```bash
# Terminal 1 - League Manager
cd agents/league_manager
python main.py --port 8000

# Expected output:
# [INFO] League Manager starting on port 8000
# [INFO] MCP server initialized
# [INFO] Listening for registrations...
```

League Manager listens for POST requests at `http://localhost:8000/mcp`.

**Verification:**

```bash
# Test League Manager is running
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "agent": "league_manager", "version": "1.0.0"}
```

### 3.3 Terminals 2-3 – Referees

**Starting Referees:**

```bash
# Terminal 2 - Referee REF01
cd agents/referee_REF01
python main.py --port 8001

# Terminal 3 - Referee REF02
cd agents/referee_REF02
python main.py --port 8002
```

**Expected output for each referee:**

```
[INFO] Referee starting on port 8001
[INFO] MCP server initialized
[INFO] Sending registration to League Manager...
[INFO] Registration successful: referee_id=REF01
[INFO] Auth token received: tok_ref01_abc123
[INFO] Ready to manage games
```

Each referee, upon startup, executes a `register_to_league()` function that sends `REFEREE_REGISTER_REQUEST` to the League Manager.

### 3.4 Terminals 4-7 – Players

**Starting Players:**

```bash
# Terminal 4 - Player P01
cd agents/player_P01
python main.py --port 8101

# Terminal 5 - Player P02
cd agents/player_P02
python main.py --port 8102

# Terminal 6 - Player P03
cd agents/player_P03
python main.py --port 8103

# Terminal 7 - Player P04
cd agents/player_P04
python main.py --port 8104
```

**Expected output for each player:**

```
[INFO] Player Agent starting on port 8101
[INFO] MCP server initialized
[INFO] Sending registration to League Manager...
[INFO] Registration successful: player_id=P01
[INFO] Auth token received: tok_p01_xyz789
[INFO] Waiting for round announcements...
```

Each player sends `LEAGUE_REGISTER_REQUEST` to the League Manager.

### 3.5 Automated Startup Scripts

**Linux/Mac (`run_league.sh`):**

```bash
#!/bin/bash

# Start League Manager
cd agents/league_manager && python main.py --port 8000 &
LEAGUE_PID=$!
sleep 2

# Start Referees
cd ../referee_REF01 && python main.py --port 8001 &
cd ../referee_REF02 && python main.py --port 8002 &
sleep 2

# Start Players
cd ../player_P01 && python main.py --port 8101 &
cd ../player_P02 && python main.py --port 8102 &
cd ../player_P03 && python main.py --port 8103 &
cd ../player_P04 && python main.py --port 8104 &

echo "All agents started. League Manager PID: $LEAGUE_PID"
```

**Windows (`run_league.bat`):**

```batch
@echo off
start "League Manager" cmd /k "cd agents\league_manager && python main.py --port 8000"
timeout /t 2

start "Referee REF01" cmd /k "cd agents\referee_REF01 && python main.py --port 8001"
start "Referee REF02" cmd /k "cd agents\referee_REF02 && python main.py --port 8002"
timeout /t 2

start "Player P01" cmd /k "cd agents\player_P01 && python main.py --port 8101"
start "Player P02" cmd /k "cd agents\player_P02 && python main.py --port 8102"
start "Player P03" cmd /k "cd agents\player_P03 && python main.py --port 8103"
start "Player P04" cmd /k "cd agents\player_P04 && python main.py --port 8104"

echo All agents started in separate windows
```

---

## 4. Stage 1: Referee Registration

Each referee, immediately upon server startup, makes a client-side call to the League Manager.

### 4.1 Referee Registration Request

**Message Type:** `REFEREE_REGISTER_REQUEST`

**Request (from Referee REF01 to League Manager):**

```json
{
  "jsonrpc": "2.0",
  "method": "register_referee",
  "params": {
    "protocol": "league.v2",
    "message_type": "REFEREE_REGISTER_REQUEST",
    "sender": "referee:alpha",
    "timestamp": "20250115T10:00:00Z",
    "conversation_id": "convrefalphareg001",
    "referee_meta": {
      "display_name": "Referee Alpha",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "contact_endpoint": "http://localhost:8001/mcp",
      "max_concurrent_matches": 2
    }
  },
  "id": 1
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | Temporary identifier before registration |
| `referee_meta.display_name` | string | Human-readable name for logs |
| `referee_meta.version` | string | Referee implementation version |
| `referee_meta.game_types` | array | Supported game types |
| `referee_meta.contact_endpoint` | string | HTTP endpoint for receiving messages |
| `referee_meta.max_concurrent_matches` | int | Capacity limit for match assignments |

### 4.2 League Manager Response

**Message Type:** `REFEREE_REGISTER_RESPONSE`

**Response (from League Manager to Referee):**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "REFEREE_REGISTER_RESPONSE",
    "sender": "league_manager",
    "timestamp": "20250115T10:00:01Z",
    "conversation_id": "convrefalphareg001",
    "status": "ACCEPTED",
    "referee_id": "REF01",
    "auth_token": "tok_ref01_abc123",
    "league_id": "league_2025_even_odd",
    "reason": null
  },
  "id": 1
}
```

**Key Response Fields:**

| Field | Description |
|-------|-------------|
| `status` | "ACCEPTED" or "REJECTED" |
| `referee_id` | Unique identifier assigned by League Manager |
| `auth_token` | Authentication token for future requests |
| `league_id` | League this referee is assigned to |
| `reason` | Explanation if rejected (null if accepted) |

**Second Referee Registration:**

The second referee (on port 8002) sends a similar request and receives:
- `referee_id`: "REF02"
- `auth_token`: "tok_ref02_def456"

### 4.3 League Manager Internal State Update

After successful registration, League Manager updates:

```python
# Internal referee registry
self.referees = {
    "REF01": {
        "endpoint": "http://localhost:8001/mcp",
        "auth_token": "tok_ref01_abc123",
        "game_types": ["even_odd"],
        "status": "AVAILABLE",
        "current_matches": []
    },
    "REF02": {
        "endpoint": "http://localhost:8002/mcp",
        "auth_token": "tok_ref02_def456",
        "game_types": ["even_odd"],
        "status": "AVAILABLE",
        "current_matches": []
    }
}
```

---

## 5. Stage 2: Player Registration

After referees are registered, each player sends a registration request.

### 5.1 Player Registration Request

**Message Type:** `LEAGUE_REGISTER_REQUEST`

**Request (from Player P01 to League Manager):**

```json
{
  "jsonrpc": "2.0",
  "method": "register_player",
  "params": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_REGISTER_REQUEST",
    "sender": "player:alpha",
    "timestamp": "20250115T10:05:00Z",
    "conversation_id": "convplayeralphareg001",
    "player_meta": {
      "display_name": "Agent Alpha",
      "version": "1.0.0",
      "game_types": ["even_odd"],
      "contact_endpoint": "http://localhost:8101/mcp"
    }
  },
  "id": 1
}
```

**Field Descriptions:**

| Field | Type | Description |
|-------|------|-------------|
| `sender` | string | Temporary identifier before registration |
| `player_meta.display_name` | string | Display name for standings and logs |
| `player_meta.version` | string | Player agent implementation version |
| `player_meta.game_types` | array | Game types this player can participate in |
| `player_meta.contact_endpoint` | string | HTTP endpoint for receiving invitations |

### 5.2 League Manager Response

**Message Type:** `LEAGUE_REGISTER_RESPONSE`

**Response (from League Manager to Player P01):**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_REGISTER_RESPONSE",
    "sender": "league_manager",
    "timestamp": "20250115T10:05:01Z",
    "conversation_id": "convplayeralphareg001",
    "status": "ACCEPTED",
    "player_id": "P01",
    "auth_token": "tok_p01_xyz789",
    "league_id": "league_2025_even_odd",
    "reason": null
  },
  "id": 1
}
```

### 5.3 All Player Registrations

**Complete registration results:**

| Player | Port | player_id | auth_token | display_name |
|--------|------|-----------|------------|--------------|
| Alpha  | 8101 | P01       | tok_p01_xyz789 | Agent Alpha |
| Beta   | 8102 | P02       | tok_p02_def456 | Agent Beta |
| Gamma  | 8103 | P03       | tok_p03_ghi012 | Agent Gamma |
| Delta  | 8104 | P04       | tok_p04_jkl345 | Agent Delta |

### 5.4 League Manager Internal State Update

League Manager maintains a map: `player_id → contact_endpoint`

```python
self.players = {
    "P01": {
        "endpoint": "http://localhost:8101/mcp",
        "auth_token": "tok_p01_xyz789",
        "display_name": "Agent Alpha",
        "stats": {"wins": 0, "losses": 0, "draws": 0, "points": 0}
    },
    "P02": { ... },
    "P03": { ... },
    "P04": { ... }
}
```

---

## 6. Stage 3: Creating Game Schedule

After all players and referees are registered, League Manager executes **Round-Robin scheduling** logic on the player list.

### 6.1 Round-Robin Algorithm

For **4 players**, the algorithm generates:

**Total matches:** `n * (n-1) / 2 = 4 * 3 / 2 = 6 matches`

**Distribution across rounds:**
- Round 1: 2 matches (P01 vs P02, P03 vs P04)
- Round 2: 2 matches (P03 vs P01, P04 vs P02)
- Round 3: 2 matches (P04 vs P01, P03 vs P02)

### 6.2 Complete Schedule

**Table 2: Game Schedule**

| Match ID | Round | Player A | Player B | Referee |
|----------|-------|----------|----------|---------|
| R1M1     | 1     | P01      | P02      | REF01   |
| R1M2     | 1     | P03      | P04      | REF01   |
| R2M1     | 2     | P03      | P01      | REF02   |
| R2M2     | 2     | P04      | P02      | REF02   |
| R3M1     | 3     | P04      | P01      | REF01   |
| R3M2     | 3     | P03      | P02      | REF01   |

### 6.3 Schedule Persistence

League Manager writes schedule to:

**File:** `SHARED/data/leagues/league_2025_even_odd/schedule.json`

```json
{
  "id": "league_2025_even_odd",
  "schema_version": "1.0",
  "last_updated": "2025-01-15T10:10:00Z",
  "rounds": [
    {
      "round_id": 1,
      "matches": [
        {
          "match_id": "R1M1",
          "player_A_id": "P01",
          "player_B_id": "P02",
          "referee_id": "REF01"
        },
        {
          "match_id": "R1M2",
          "player_A_id": "P03",
          "player_B_id": "P04",
          "referee_id": "REF01"
        }
      ]
    },
    {
      "round_id": 2,
      "matches": [ ... ]
    },
    {
      "round_id": 3,
      "matches": [ ... ]
    }
  ]
}
```

---

## 7. Stage 4: Round Announcement

League Manager sends `ROUND_ANNOUNCEMENT` message to **all players**.

### 7.1 Round Announcement Message

**Message Type:** `ROUND_ANNOUNCEMENT`

**Request (from League Manager to all players):**

```json
{
  "jsonrpc": "2.0",
  "method": "notify_round",
  "params": {
    "protocol": "league.v2",
    "message_type": "ROUND_ANNOUNCEMENT",
    "sender": "league_manager",
    "timestamp": "20250115T10:10:00Z",
    "conversation_id": "convround1announce",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "matches": [
      {
        "match_id": "R1M1",
        "game_type": "even_odd",
        "player_A_id": "P01",
        "player_B_id": "P02",
        "referee_endpoint": "http://localhost:8001/mcp"
      },
      {
        "match_id": "R1M2",
        "game_type": "even_odd",
        "player_A_id": "P03",
        "player_B_id": "P04",
        "referee_endpoint": "http://localhost:8001/mcp"
      }
    ]
  },
  "id": 10
}
```

### 7.2 Player Acknowledgment

Each player logs the announcement and prepares for game invitations:

```python
def handle_round_announcement(params):
    round_id = params["round_id"]
    matches = params["matches"]

    # Find matches I'm participating in
    my_matches = [m for m in matches if
                  m["player_A_id"] == self.player_id or
                  m["player_B_id"] == self.player_id]

    logger.info(f"Round {round_id} announced: {len(my_matches)} matches")

    return {"acknowledged": True}
```

### 7.3 League Manager State Transition

Once `ROUND_ANNOUNCEMENT` is sent:
- Round status: `ANNOUNCED`
- Next step: Referees can begin sending game invitations

---

## 8. Stage 5: Managing a Single Game

We'll describe the flow of game **R1M1**: Player P01 vs Player P02, Referee REF01.

### 8.1 Game State Machine

```
WAITING_FOR_PLAYERS → COLLECTING_CHOICES → DRAWING_NUMBER → EVALUATING → FINISHED
```

### 8.2 Stage 5.1: Game Invitation

Referee transitions game state to `WAITING_FOR_PLAYERS` and sends `GAME_INVITATION` to each player.

**Invitation to P01:**

```json
{
  "jsonrpc": "2.0",
  "method": "handle_game_invitation",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_INVITATION",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:15:00Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_ref01_abc123",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "match_id": "R1M1",
    "game_type": "even_odd",
    "role_in_match": "PLAYER_A",
    "opponent_id": "P02"
  },
  "id": 1001
}
```

**Invitation to P02:**

```json
{
  "jsonrpc": "2.0",
  "method": "handle_game_invitation",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_INVITATION",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:15:00Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_ref01_abc123",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "match_id": "R1M1",
    "game_type": "even_odd",
    "role_in_match": "PLAYER_B",
    "opponent_id": "P01"
  },
  "id": 1002
}
```

**Key differences:**
- `role_in_match`: "PLAYER_A" vs "PLAYER_B"
- `opponent_id`: Different for each player

### 8.3 Stage 5.2: Arrival Confirmations

Each player returns `GAME_JOIN_ACK` within **5 seconds**.

**Confirmation from P01:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "GAME_JOIN_ACK",
    "sender": "player:P01",
    "timestamp": "20250115T10:15:01Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_p01_xyz789",
    "match_id": "R1M1",
    "player_id": "P01",
    "arrival_timestamp": "20250115T10:15:01Z",
    "accept": true
  },
  "id": 1001
}
```

**Confirmation from P02:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "GAME_JOIN_ACK",
    "sender": "player:P02",
    "timestamp": "20250115T10:15:02Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_p02_def456",
    "match_id": "R1M1",
    "player_id": "P02",
    "arrival_timestamp": "20250115T10:15:02Z",
    "accept": true
  },
  "id": 1002
}
```

**Referee Logic:**

```python
def wait_for_players():
    timeout = 5  # seconds
    start_time = time.time()

    acks = {}
    while len(acks) < 2 and (time.time() - start_time) < timeout:
        # Wait for ACKs from both players
        pass

    if len(acks) == 2 and all(ack["accept"] for ack in acks.values()):
        # Both accepted - proceed to COLLECTING_CHOICES
        self.game_state = "COLLECTING_CHOICES"
        return True
    else:
        # Timeout or rejection - abort game
        self.abort_game(reason="PLAYER_NO_SHOW")
        return False
```

When referee receives both positive ACKs within allowed time, it transitions game state to `COLLECTING_CHOICES`.

### 8.4 Stage 5.3: Collecting Choices

Referee sends `CHOOSE_PARITY_CALL` to each player.

**Choice Request to P01:**

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
    "player_id": "P01",
    "game_type": "even_odd",
    "context": {
      "opponent_id": "P02",
      "round_id": 1,
      "your_standings": {
        "wins": 0,
        "losses": 0,
        "draws": 0
      }
    },
    "deadline": "20250115T10:15:35Z"
  },
  "id": 1101
}
```

**Response from P01 (chose "even"):**

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

**Response from P02 (chose "odd"):**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "CHOOSE_PARITY_RESPONSE",
    "sender": "player:P02",
    "timestamp": "20250115T10:15:12Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_p02_def456",
    "match_id": "R1M1",
    "player_id": "P02",
    "parity_choice": "odd"
  },
  "id": 1102
}
```

**Timeout handling:**

- Deadline: 30 seconds from request
- If player doesn't respond: Technical loss (forfeit)
- If invalid choice (not "even" or "odd"): Technical loss

When both choices are received correctly and on time, referee transitions game state to `DRAWING_NUMBER`.

### 8.5 Stage 5.4: Drawing Number and Determining Winner

Referee draws a number between 1-10 using cryptographic randomness.

**Referee Logic:**

```python
import secrets

def draw_and_evaluate():
    # Draw number (1-10)
    drawn_number = secrets.randbelow(10) + 1  # Range: 1-10

    # Determine parity
    number_parity = "even" if drawn_number % 2 == 0 else "odd"

    # Get player choices
    p01_choice = "even"  # from CHOOSE_PARITY_RESPONSE
    p02_choice = "odd"   # from CHOOSE_PARITY_RESPONSE

    # Determine winner
    if p01_choice == number_parity:
        winner_player_id = "P01"
        status = "WIN"
    elif p02_choice == number_parity:
        winner_player_id = "P02"
        status = "WIN"
    else:
        # Both wrong (impossible in this game)
        winner_player_id = None
        status = "DRAW"

    # Transition to FINISHED
    self.game_state = "FINISHED"

    return {
        "drawn_number": drawn_number,
        "number_parity": number_parity,
        "winner_player_id": winner_player_id,
        "status": status
    }
```

**Example execution:**
- `drawn_number = 8`
- `number_parity = "even"`
- P01 choice = "even" ✓ (Correct!)
- P02 choice = "odd" ✗ (Wrong!)
- **Winner:** P01
- **Status:** WIN

Game state transitions to `FINISHED`.

### 8.6 Stage 5.5: Game End Notification to Players

Referee sends `GAME_OVER` to **both players**:

```json
{
  "jsonrpc": "2.0",
  "method": "notify_match_result",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_OVER",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:15:30Z",
    "conversation_id": "convr1m1001",
    "auth_token": "tok_ref01_abc123",
    "match_id": "R1M1",
    "game_type": "even_odd",
    "game_result": {
      "status": "WIN",
      "winner_player_id": "P01",
      "drawn_number": 8,
      "number_parity": "even",
      "choices": {
        "P01": "even",
        "P02": "odd"
      },
      "reason": "P01 chose even, number was 8 (even)"
    }
  },
  "id": 1201
}
```

**Player Response (fire-and-forget):**

Each player updates internal state (statistics, history) and returns acknowledgment:

```python
def handle_match_result(params):
    result = params["game_result"]

    # Update match history
    self.update_history({
        "match_id": params["match_id"],
        "opponent_id": params["game_result"]["choices"].keys() - {self.player_id},
        "my_choice": result["choices"][self.player_id],
        "drawn_number": result["drawn_number"],
        "won": result["winner_player_id"] == self.player_id
    })

    # Update opponent profile for learning
    self.update_opponent_profile(opponent_id, opponent_choice)

    return {"acknowledged": True}
```

### 8.7 Stage 5.6: Report to League Manager

Referee reports `MATCH_RESULT_REPORT` to the league:

```json
{
  "jsonrpc": "2.0",
  "method": "report_match_result",
  "params": {
    "protocol": "league.v2",
    "message_type": "MATCH_RESULT_REPORT",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:15:35Z",
    "conversation_id": "convr1m1report",
    "auth_token": "tok_ref01_abc123",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "match_id": "R1M1",
    "game_type": "even_odd",
    "result": {
      "winner": "P01",
      "score": {
        "P01": 3,
        "P02": 0
      },
      "details": {
        "drawn_number": 8,
        "choices": {
          "P01": "even",
          "P02": "odd"
        }
      }
    }
  },
  "id": 1301
}
```

**League Manager Updates:**

```python
def handle_match_result_report(params):
    result = params["result"]

    # Update standings
    if result["winner"]:
        self.players[result["winner"]]["stats"]["wins"] += 1
        self.players[result["winner"]]["stats"]["points"] += 3

        # Determine loser
        loser = [p for p in result["score"].keys() if p != result["winner"]][0]
        self.players[loser]["stats"]["losses"] += 1
    else:
        # Draw (impossible in Even/Odd, but handle generically)
        for player_id in result["score"].keys():
            self.players[player_id]["stats"]["draws"] += 1
            self.players[player_id]["stats"]["points"] += 1

    # Mark match as complete
    self.mark_match_complete(params["match_id"])

    # Check if round is complete
    if self.all_round_matches_complete(params["round_id"]):
        self.finalize_round(params["round_id"])
```

---

## 9. Stage 6: Round Completion and Standings Update

Round 1 ends when `MATCH_RESULT_REPORT` is received for **all round matches**.

### 9.1 Round Completion Logic

```python
def all_round_matches_complete(round_id):
    round_matches = self.schedule["rounds"][round_id - 1]["matches"]
    completed = [m for m in round_matches if m["status"] == "COMPLETED"]
    return len(completed) == len(round_matches)

def finalize_round(round_id):
    # 1. Calculate standings
    standings = self.calculate_standings()

    # 2. Send standings update to all players
    self.send_standings_update(round_id, standings)

    # 3. Send round completion notification
    self.send_round_completed(round_id)

    # 4. Check if league is complete
    if round_id == self.total_rounds:
        self.finalize_league()
```

### 9.2 Standings Calculation

League Manager calculates standings after Round 1:

**Table 3: Standings After Round 1**

| Rank | Player ID | Display Name | Played | Wins | Draws | Losses | Points |
|------|-----------|--------------|--------|------|-------|--------|--------|
| 1    | P01       | Agent Alpha  | 1      | 1    | 0     | 0      | 3      |
| 2    | P03       | Agent Gamma  | 1      | 0    | 1     | 0      | 1      |
| 3    | P04       | Agent Delta  | 1      | 0    | 1     | 0      | 1      |
| 4    | P02       | Agent Beta   | 1      | 0    | 0     | 1      | 0      |

**Scoring rules:**
- Win: 3 points
- Draw: 1 point
- Loss: 0 points

**Tiebreaker order:**
1. Total points
2. Head-to-head result (if applicable)
3. Alphabetical by player_id

### 9.3 Standings Update Message

**Message Type:** `LEAGUE_STANDINGS_UPDATE`

```json
{
  "jsonrpc": "2.0",
  "method": "update_standings",
  "params": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_STANDINGS_UPDATE",
    "sender": "league_manager",
    "timestamp": "20250115T10:20:00Z",
    "conversation_id": "convround1standings",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "standings": [
      {
        "rank": 1,
        "player_id": "P01",
        "display_name": "Agent Alpha",
        "played": 1,
        "wins": 1,
        "draws": 0,
        "losses": 0,
        "points": 3
      },
      {
        "rank": 2,
        "player_id": "P03",
        "display_name": "Agent Gamma",
        "played": 1,
        "wins": 0,
        "draws": 1,
        "losses": 0,
        "points": 1
      },
      {
        "rank": 3,
        "player_id": "P04",
        "display_name": "Agent Delta",
        "played": 1,
        "wins": 0,
        "draws": 1,
        "losses": 0,
        "points": 1
      },
      {
        "rank": 4,
        "player_id": "P02",
        "display_name": "Agent Beta",
        "played": 1,
        "wins": 0,
        "draws": 0,
        "losses": 1,
        "points": 0
      }
    ]
  },
  "id": 1401
}
```

### 9.4 Round Completed Message

After sending standings update, League Manager sends `ROUND_COMPLETED` message:

```json
{
  "jsonrpc": "2.0",
  "method": "notify_round_completed",
  "params": {
    "protocol": "league.v2",
    "message_type": "ROUND_COMPLETED",
    "sender": "league_manager",
    "timestamp": "20250115T10:20:05Z",
    "conversation_id": "convround1complete",
    "league_id": "league_2025_even_odd",
    "round_id": 1,
    "matches_played": 2,
    "next_round_id": 2
  },
  "id": 1402
}
```

### 9.5 Data Persistence

League Manager writes updated standings to:

**File:** `SHARED/data/leagues/league_2025_even_odd/standings.json`

```json
{
  "id": "league_2025_even_odd",
  "schema_version": "1.0",
  "last_updated": "2025-01-15T10:20:00Z",
  "current_round": 1,
  "standings": [
    {
      "rank": 1,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "played": 1,
      "wins": 1,
      "draws": 0,
      "losses": 0,
      "points": 3
    },
    ...
  ]
}
```

---

## 10. Stage 7: League Completion

After **all rounds** are complete (rounds 1, 2, 3 for 4 players), League Manager finalizes the league.

### 10.1 Final Standings

**Table 4: Final Standings After Round 3**

| Rank | Player ID | Display Name | Played | Wins | Draws | Losses | Points |
|------|-----------|--------------|--------|------|-------|--------|--------|
| 1    | P01       | Agent Alpha  | 3      | 2    | 1     | 0      | 7      |
| 2    | P03       | Agent Gamma  | 3      | 1    | 2     | 0      | 5      |
| 3    | P04       | Agent Delta  | 3      | 1    | 1     | 1      | 4      |
| 4    | P02       | Agent Beta   | 3      | 0    | 0     | 3      | 0      |

### 10.2 League Completed Message

**Message Type:** `LEAGUE_COMPLETED`

```json
{
  "jsonrpc": "2.0",
  "method": "notify_league_completed",
  "params": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_COMPLETED",
    "sender": "league_manager",
    "timestamp": "20250115T12:00:00Z",
    "conversation_id": "convleaguecomplete",
    "league_id": "league_2025_even_odd",
    "total_rounds": 3,
    "total_matches": 6,
    "champion": {
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "points": 7
    },
    "final_standings": [
      {"rank": 1, "player_id": "P01", "points": 7},
      {"rank": 2, "player_id": "P03", "points": 5},
      {"rank": 3, "player_id": "P04", "points": 4},
      {"rank": 4, "player_id": "P02", "points": 2}
    ]
  },
  "id": 2001
}
```

### 10.3 League Archival

League Manager archives all data:

1. **Final standings** → `SHARED/data/leagues/league_2025_even_odd/final_standings.json`
2. **All match transcripts** → `SHARED/data/matches/league_2025_even_odd/`
3. **Complete logs** → `SHARED/logs/league/league_2025_even_odd/`

---

## 11. Error Handling

When an error occurs, League Manager or Referee sends appropriate error message.

### 11.1 Authentication Error

**Message Type:** `LEAGUE_ERROR`

**Scenario:** Player sends request with invalid auth token

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_ERROR",
    "sender": "league_manager",
    "timestamp": "20250115T10:05:30Z",
    "conversation_id": "converror001",
    "error_code": "E012",
    "error_description": "AUTH_TOKEN_INVALID",
    "context": {
      "provided_token": "tok_invalid_xxx",
      "action": "LEAGUE_QUERY"
    }
  },
  "id": 1502
}
```

**Player action:** Request new auth token via re-registration

### 11.2 Timeout Error

**Message Type:** `GAME_ERROR`

**Scenario:** Player doesn't respond to CHOOSE_PARITY_CALL within 30 seconds

```json
{
  "jsonrpc": "2.0",
  "method": "notify_game_error",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_ERROR",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:16:00Z",
    "conversation_id": "convr1m1001",
    "match_id": "R1M1",
    "error_code": "E001",
    "error_description": "TIMEOUT_ERROR",
    "affected_player": "P02",
    "action_required": "CHOOSE_PARITY_RESPONSE",
    "retry_count": 0,
    "max_retries": 3,
    "consequence": "Technical loss if no response after retries"
  },
  "id": 1103
}
```

**Referee action:**
- Retry up to 3 times (max_retries)
- After 3 failed attempts → award technical loss to P02

### 11.3 Invalid Choice Error

**Scenario:** Player sends invalid parity choice ("maybe" instead of "even"/"odd")

```json
{
  "jsonrpc": "2.0",
  "method": "notify_game_error",
  "params": {
    "protocol": "league.v2",
    "message_type": "GAME_ERROR",
    "sender": "referee:REF01",
    "timestamp": "20250115T10:15:15Z",
    "conversation_id": "convr1m1001",
    "match_id": "R1M1",
    "error_code": "E002",
    "error_description": "INVALID_CHOICE",
    "affected_player": "P02",
    "context": {
      "received_choice": "maybe",
      "valid_choices": ["even", "odd"]
    },
    "consequence": "Technical loss due to protocol violation"
  },
  "id": 1104
}
```

**Referee action:** Award technical loss immediately (no retry)

### 11.4 Error Code Catalog

**Table 5: Error Codes**

| Code | Description | Severity | Action |
|------|-------------|----------|--------|
| E001 | TIMEOUT_ERROR | Medium | Retry up to 3 times |
| E002 | INVALID_CHOICE | High | Immediate forfeit |
| E003 | PLAYER_NO_SHOW | High | Immediate forfeit |
| E012 | AUTH_TOKEN_INVALID | High | Re-authenticate |
| E021 | PROTOCOL_VERSION_MISMATCH | Critical | Update agent |
| E099 | INTERNAL_SERVER_ERROR | Critical | Contact admin |

---

## 12. Available Query Tools

The protocol defines generic MCP tools that any agent can expose for debugging and inquiry purposes.

### 12.1 Standings Query

**Tool:** `league_query` (League Manager)

**Scenario:** A player wants to verify their ranking

**Request (from Player P01 to League Manager):**

```json
{
  "jsonrpc": "2.0",
  "method": "league_query",
  "params": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_QUERY",
    "sender": "player:P01",
    "timestamp": "20250115T10:25:00Z",
    "conversation_id": "convquerystandings001",
    "auth_token": "tok_p01_xyz789",
    "league_id": "league_2025_even_odd",
    "query_type": "GET_STANDINGS"
  },
  "id": 1501
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "LEAGUE_QUERY_RESPONSE",
    "sender": "league_manager",
    "timestamp": "20250115T10:25:01Z",
    "conversation_id": "convquerystandings001",
    "standings": [
      {"rank": 1, "player_id": "P01", "points": 3, "wins": 1, "draws": 0, "losses": 0},
      {"rank": 2, "player_id": "P03", "points": 1, "wins": 0, "draws": 1, "losses": 0},
      {"rank": 3, "player_id": "P04", "points": 1, "wins": 0, "draws": 1, "losses": 0},
      {"rank": 4, "player_id": "P02", "points": 0, "wins": 0, "draws": 0, "losses": 1}
    ]
  },
  "id": 1501
}
```

### 12.2 Match State Query

**Tool:** `get_match_state` (Referee)

**Scenario:** Debugging stuck game

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "get_match_state",
  "params": {
    "match_id": "R1M1",
    "auth_token": "tok_admin_debug"
  },
  "id": 1601
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "match_id": "R1M1",
    "state": "COLLECTING_CHOICES",
    "players": {
      "P01": {"status": "CHOICE_RECEIVED", "choice": "even"},
      "P02": {"status": "WAITING", "choice": null}
    },
    "deadline": "20250115T10:15:35Z",
    "time_remaining": 18
  },
  "id": 1601
}
```

### 12.3 Player History Query

**Tool:** `get_player_state` (Player Agent)

**Scenario:** Analyzing opponent patterns

**Request:**

```json
{
  "jsonrpc": "2.0",
  "method": "get_player_state",
  "params": {
    "player_id": "P01",
    "auth_token": "tok_p01_xyz789"
  },
  "id": 1701
}
```

**Response:**

```json
{
  "jsonrpc": "2.0",
  "result": {
    "player_id": "P01",
    "total_matches": 15,
    "win_rate": 0.67,
    "opponent_profiles": {
      "P02": {
        "matches_played": 5,
        "even_frequency": 0.8,
        "pattern_detected": true
      },
      "P03": {
        "matches_played": 5,
        "even_frequency": 0.5,
        "pattern_detected": false
      }
    }
  },
  "id": 1701
}
```

### 12.4 Additional Tools

**Table 6: Query Tools by Agent**

| Agent | Tool Name | Purpose | Auth Required |
|-------|-----------|---------|---------------|
| League Manager | `league_query` | Get standings, schedule, round status | Yes (player token) |
| Referee | `get_match_state` | Debug game state | Yes (referee/admin token) |
| Player | `get_player_state` | Access own history and stats | Yes (player token) |
| Player | `get_opponent_profile` | Get opponent pattern analysis | Yes (player token) |

---

## 13. Complete Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         START                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│             League Manager Starts (Port 8000)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│       Referees Start and Register (Ports 8001-8002)          │
│       • Send REFEREE_REGISTER_REQUEST                        │
│       • Receive referee_id + auth_token                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│       Players Start and Register (Ports 8101-8104)           │
│       • Send LEAGUE_REGISTER_REQUEST                         │
│       • Receive player_id + auth_token                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│               Create Round-Robin Schedule                    │
│       • 4 players = 6 matches across 3 rounds                │
│       • Assign referees to matches                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                 ROUND_ANNOUNCEMENT (Round 1)                 │
│       • Sent to all players                                  │
│       • Includes match schedule                              │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │   More Matches in Current Round?      │
        └───────────────────────────────────────┘
                 Yes ↓               ↓ No
        ┌─────────────────┐    ┌──────────────────────┐
        │   RUN MATCH     │    │ FINALIZE ROUND       │
        │   (see below)   │    │ • Calculate standings│
        └─────────────────┘    │ • Send standings     │
                 ↓             │ • Send ROUND_COMPLETE│
                 │             └──────────────────────┘
                 │                      ↓
                 └──────────────────────┘
                            ↓
        ┌───────────────────────────────────────┐
        │         More Rounds?                  │
        └───────────────────────────────────────┘
                 Yes ↓               ↓ No
         (loop to ROUND_ANNOUNCEMENT)
                                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   LEAGUE_COMPLETED                           │
│       • Announce champion                                    │
│       • Send final standings                                 │
│       • Archive all data                                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                          END                                 │
└─────────────────────────────────────────────────────────────┘
```

### 13.1 RUN MATCH Subflow

```
┌─────────────────────────────────────────────────────────────┐
│                    RUN MATCH (R1M1)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   GAME_INVITATION (to both players)                          │
│   • Timeout: 5 seconds                                       │
│   • State: WAITING_FOR_PLAYERS                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   GAME_JOIN_ACK (from both players)                          │
│   • Both accept=true → proceed                               │
│   • Any reject/timeout → abort game                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   CHOOSE_PARITY_CALL (to both players)                       │
│   • Timeout: 30 seconds                                      │
│   • State: COLLECTING_CHOICES                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   CHOOSE_PARITY_RESPONSE (from both players)                 │
│   • Valid choices: "even" or "odd"                           │
│   • Invalid/timeout → technical loss                         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   DRAW NUMBER (1-10, cryptographic random)                   │
│   • Determine parity: even/odd                               │
│   • State: DRAWING_NUMBER → EVALUATING                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   DETERMINE WINNER                                           │
│   • Compare player choices to number parity                  │
│   • Winner gets 3 points, loser gets 0 points                │
│   • State: FINISHED                                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   GAME_OVER (to both players)                                │
│   • Include result, drawn number, choices                    │
│   • Players update internal state                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│   MATCH_RESULT_REPORT (to League Manager)                    │
│   • League Manager updates standings                         │
│   • Match marked as complete                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
                   (Return to main flow)
```

---

## 14. Agent Roles Reference

**Table 7: Agent Roles in System**

| Agent | Port | Role in League | Communicates With | Key Responsibilities |
|-------|------|----------------|-------------------|---------------------|
| League Manager | 8000 | League Orchestrator | Referees, Players | • Player/referee registration<br>• Schedule creation<br>• Standings management<br>• Round coordination |
| Referee REF01 | 8001 | Game Orchestrator | League Manager, Players | • Game state management<br>• Rule enforcement<br>• Result reporting |
| Referee REF02 | 8002 | Game Orchestrator | League Manager, Players | • Game state management<br>• Rule enforcement<br>• Result reporting |
| Player P01 | 8101 | Player Agent | Referee, League Manager | • Accept invitations<br>• Make parity choices<br>• Learn from results |
| Player P02 | 8102 | Player Agent | Referee, League Manager | • Accept invitations<br>• Make parity choices<br>• Learn from results |
| Player P03 | 8103 | Player Agent | Referee, League Manager | • Accept invitations<br>• Make parity choices<br>• Learn from results |
| Player P04 | 8104 | Player Agent | Referee, League Manager | • Accept invitations<br>• Make parity choices<br>• Learn from results |

---

## 15. Monitoring and Debugging

### 15.1 Real-Time Monitoring Script

**File:** `scripts/monitor_tournament.py`

```python
#!/usr/bin/env python3
"""
Real-time tournament monitoring dashboard.
Displays live standings, match progress, and error logs.
"""

import requests
import time
import os
from datetime import datetime

LEAGUE_MANAGER_URL = "http://localhost:8000/mcp"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_standings():
    response = requests.post(LEAGUE_MANAGER_URL, json={
        "jsonrpc": "2.0",
        "method": "league_query",
        "params": {
            "query_type": "GET_STANDINGS",
            "league_id": "league_2025_even_odd"
        },
        "id": 1
    })
    return response.json()["result"]["standings"]

def get_current_round():
    response = requests.post(LEAGUE_MANAGER_URL, json={
        "jsonrpc": "2.0",
        "method": "league_query",
        "params": {
            "query_type": "GET_CURRENT_ROUND",
            "league_id": "league_2025_even_odd"
        },
        "id": 2
    })
    return response.json()["result"]

def display_dashboard():
    while True:
        clear_screen()

        print("=" * 80)
        print(f"{'EVEN/ODD LEAGUE TOURNAMENT DASHBOARD':^80}")
        print(f"{'Updated: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^80}")
        print("=" * 80)

        # Current round
        round_info = get_current_round()
        print(f"\nCurrent Round: {round_info['round_id']} of {round_info['total_rounds']}")
        print(f"Matches Completed: {round_info['completed_matches']} of {round_info['total_matches']}")

        # Standings
        print("\n" + "-" * 80)
        print(f"{'CURRENT STANDINGS':^80}")
        print("-" * 80)
        print(f"{'Rank':<6}{'Player':<15}{'Played':<8}{'W':<4}{'D':<4}{'L':<4}{'Points':<8}")
        print("-" * 80)

        standings = get_standings()
        for player in standings:
            print(f"{player['rank']:<6}"
                  f"{player['display_name']:<15}"
                  f"{player['played']:<8}"
                  f"{player['wins']:<4}"
                  f"{player['draws']:<4}"
                  f"{player['losses']:<4}"
                  f"{player['points']:<8}")

        print("=" * 80)
        print("\nPress Ctrl+C to exit")

        time.sleep(2)  # Update every 2 seconds

if __name__ == "__main__":
    try:
        display_dashboard()
    except KeyboardInterrupt:
        print("\n\nMonitoring stopped.")
```

**Usage:**

```bash
python scripts/monitor_tournament.py
```

### 15.2 Log Aggregation

**View all logs in real-time:**

```bash
# Linux/Mac
tail -f SHARED/logs/**/*.jsonl | jq '.'

# Windows (PowerShell)
Get-Content SHARED\logs\**\*.jsonl -Wait | ConvertFrom-Json
```

**Filter for errors only:**

```bash
# Linux/Mac
tail -f SHARED/logs/**/*.jsonl | jq 'select(.level == "ERROR")'

# Windows (PowerShell)
Get-Content SHARED\logs\**\*.jsonl -Wait | ConvertFrom-Json | Where-Object { $_.level -eq "ERROR" }
```

### 15.3 Health Check Script

**File:** `scripts/health_check.sh`

```bash
#!/bin/bash

echo "=== League System Health Check ==="
echo

# Check League Manager
echo -n "League Manager (8000): "
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ Running"
else
    echo "✗ Not responding"
fi

# Check Referees
for port in 8001 8002; do
    echo -n "Referee ($port): "
    if curl -s http://localhost:$port/health > /dev/null; then
        echo "✓ Running"
    else
        echo "✗ Not responding"
    fi
done

# Check Players
for port in 8101 8102 8103 8104; do
    echo -n "Player ($port): "
    if curl -s http://localhost:$port/health > /dev/null; then
        echo "✓ Running"
    else
        echo "✗ Not responding"
    fi
done

echo
echo "=== Health Check Complete ==="
```

**Usage:**

```bash
chmod +x scripts/health_check.sh
./scripts/health_check.sh
```

---

## 16. Troubleshooting

### 16.1 Common Issues

**Problem:** Referee registration fails with "Connection refused"

**Solution:**
```bash
# Verify League Manager is running
curl http://localhost:8000/health

# Check logs
cat SHARED/logs/system/orchestrator.log.jsonl | jq 'select(.component == "league_manager")'
```

**Problem:** Player times out during CHOOSE_PARITY_CALL

**Diagnosis:**
```bash
# Check player logs
cat SHARED/logs/agents/P01.log.jsonl | jq 'select(.match_id == "R1M1")'

# Verify player is responsive
curl -X POST http://localhost:8101/mcp -H "Content-Type: application/json" -d '{
  "jsonrpc": "2.0",
  "method": "health_check",
  "id": 1
}'
```

**Solution:**
- Check player strategy implementation for long-running operations
- Verify no blocking I/O in choose_parity handler
- Ensure LLM API calls have aggressive timeout (<25s)

**Problem:** Standings not updating after match completion

**Diagnosis:**
```bash
# Check if MATCH_RESULT_REPORT was received
cat SHARED/logs/league/league_2025_even_odd/league.log.jsonl | \
  jq 'select(.message_type == "MATCH_RESULT_REPORT")'
```

**Solution:**
- Verify referee sent MATCH_RESULT_REPORT
- Check League Manager logs for processing errors
- Manually query standings to verify data integrity

### 16.2 Emergency Shutdown

**Graceful shutdown:**

```bash
# Linux/Mac
pkill -SIGTERM -f "python.*main.py"

# Windows
taskkill /F /FI "WINDOWTITLE eq League Manager"
taskkill /F /FI "WINDOWTITLE eq Referee*"
taskkill /F /FI "WINDOWTITLE eq Player*"
```

**Force kill (use only if graceful fails):**

```bash
# Linux/Mac
pkill -9 -f "python.*main.py"

# Windows
taskkill /F /IM python.exe
```

### 16.3 Data Recovery

**If standings.json is corrupted:**

```bash
# Restore from backup
cp SHARED/data/leagues/league_2025_even_odd/backups/standings_20250115_100000.json \
   SHARED/data/leagues/league_2025_even_odd/standings.json

# Recalculate from match transcripts
python scripts/recalculate_standings.py --league-id league_2025_even_odd
```

### 16.4 Debugging Checklist

- [ ] All agents started in correct order (League Manager → Referees → Players)
- [ ] All agents registered successfully (check logs for auth_token receipt)
- [ ] Ports are not blocked by firewall
- [ ] Configuration files are valid JSON
- [ ] Timeout values are properly configured
- [ ] Log directories exist and are writable
- [ ] Python dependencies are installed
- [ ] No conflicting processes on required ports

---

## Summary

This guide presented a complete operational walkthrough for running the Even/Odd League tournament system:

✅ **System Configuration** – Port allocation, agent roles, configuration files
✅ **Startup Procedure** – Ordered startup with verification steps
✅ **Registration Flows** – Referee and player registration with auth tokens
✅ **Schedule Creation** – Round-robin algorithm for 4 players
✅ **Round Management** – Announcements, completions, standings updates
✅ **Game Flow** – Complete 6-stage game lifecycle with message examples
✅ **Error Handling** – Timeout, authentication, and validation errors
✅ **Query Tools** – Real-time standings, match state, player history
✅ **Monitoring** – Real-time dashboard, log aggregation, health checks
✅ **Troubleshooting** – Common issues and recovery procedures

**Key Principles:**

- All communication is via **JSON-RPC 2.0 over HTTP**
- All messages include **uniform envelope** (protocol, message_type, sender, timestamp UTC, conversation_id)
- **League Manager** is the orchestrator for league-level operations
- **Referees** are orchestrators for individual games
- **Players** are autonomous agents that respond to invitations and make choices
- **Error handling** is comprehensive with retries and fallbacks
- **Logging** is structured (JSON Lines) for distributed debugging
- **Data persistence** uses atomic writes with backups

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
**Maintainer:** System Architecture Team

---

**Related Documents:**
- `docs/requirements/league-system-prd.md` – League Manager requirements
- `docs/requirements/even-odd-game-prd.md` – Game rules and mechanics
- `docs/requirements/game-protocol-messages-prd.md` – All 18 message types
- `docs/requirements/developer-implementation-guide.md` – Quick start for developers
- `docs/architecture/three-layer-architecture-requirements.md` – File system architecture
