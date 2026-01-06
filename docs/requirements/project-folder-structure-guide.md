# Project Folder Structure - Developer Guide
# Organizing Your League Tournament System

**Document Version:** 1.0
**Date:** 2025-12-20
**Audience:** All Developers (Backend, DevOps, Students)
**Purpose:** Comprehensive guide to project organization and file management

---

## Table of Contents
1. [Overview: Three Base Directories](#overview-three-base-directories)
2. [SHARED/ - Shared Resources](#shared---shared-resources)
3. [agents/ - Agent Implementations](#agents---agent-implementations)
4. [doc/ - Documentation](#doc---documentation)
5. [Developer Workflows](#developer-workflows)
6. [Quick Reference Guide](#quick-reference-guide)
7. [Best Practices](#best-practices)
8. [Common Scenarios](#common-scenarios)
9. [Troubleshooting](#troubleshooting)

---

## Overview: Three Base Directories

### Base Project Structure

```
L-25-TheGame/
├── SHARED/          # Shared resources - configs, data, logs, SDK
├── agents/          # Agent code - each agent in separate folder
└── doc/             # Project documentation - specs and examples
```

### Directory Purpose Table

**Table 1: Base Project Folders**

| Folder | Description | When to Use |
|--------|-------------|-------------|
| **SHARED/** | Shared resources – configuration, data, logs, SDK library | **READ** shared configs, **WRITE** match data/logs, **USE** SDK utilities |
| **agents/** | Agent code – each agent in separate folder | **CREATE** your agent implementation here |
| **doc/** | Project documentation – specifications and examples | **REFERENCE** protocol specs, **COPY** message examples |

### Design Philosophy

**The Three Pillars:**
- **SHARED/** = "The Society" - Shared knowledge, history, and communication
- **agents/** = "The Citizens" - Individual agents with their own code
- **doc/** = "The Library" - Reference materials and examples

**Golden Rule:**
- ✅ **READ** from `SHARED/config/` (static settings)
- ✅ **READ/WRITE** to `SHARED/data/` (dynamic state)
- ✅ **WRITE** to `SHARED/logs/` (debugging/monitoring)
- ✅ **IMPLEMENT** in `agents/<your_agent>/` (your code)
- ✅ **REFERENCE** from `doc/` (specifications)

---

## 1. SHARED/ - Shared Resources

Contains all resources shared across all agents in the system.

### Complete SHARED/ Structure

```
SHARED/
├── config/              # Configuration layer (static settings)
│   ├── system.json                          # Global system settings
│   ├── agents/
│   │   └── agents_config.json              # Registry of all agents
│   ├── leagues/
│   │   └── league_2025_even_odd.json       # League-specific settings
│   ├── games/
│   │   └── games_registry.json             # Supported game types
│   └── defaults/
│       ├── referee.json                     # Default referee settings
│       └── player.json                      # Default player settings
│
├── data/                # Runtime data layer (dynamic state)
│   ├── leagues/
│   │   └── league_2025_even_odd/
│   │       ├── standings.json               # Current standings
│   │       └── rounds.json                  # Round history
│   ├── matches/
│   │   └── league_2025_even_odd/
│   │       ├── R1M1.json                    # Match R1M1 complete data
│   │       └── R1M2.json                    # Match R1M2 complete data
│   └── players/
│       ├── P01/
│       │   └── history.json                 # P01's match history
│       └── P02/
│           └── history.json                 # P02's match history
│
├── logs/                # Logging layer (tracking & debugging)
│   ├── league/
│   │   └── league_2025_even_odd/
│   │       └── league.log.jsonl            # Central league events
│   ├── agents/
│   │   ├── REF01.log.jsonl                 # Referee logs
│   │   ├── P01.log.jsonl                   # Player P01 logs
│   │   └── P02.log.jsonl                   # Player P02 logs
│   └── system/
│       └── orchestrator.log.jsonl          # System-level logs
│
└── league_sdk/          # Python SDK (shared utilities)
    ├── __init__.py
    ├── config_models.py        # Dataclass definitions
    ├── config_loader.py        # ConfigLoader class
    ├── repositories.py         # Data repositories
    └── logger.py               # JsonLogger class
```

---

### 1.A. config/ - Configuration Layer

**Purpose:** Static settings read at agent startup
**When to Use:** At agent initialization to load system-wide and agent-specific settings

#### Configuration Files Guide

**Table 2: Configuration Files Reference**

| File | When to Read | What You Get | Who Uses |
|------|--------------|--------------|----------|
| **system.json** | Agent startup | Timeouts, retry policy, network ports | All agents |
| **agents_config.json** | Registration time | List of registered players/referees | League Manager |
| **leagues/\<league_id\>.json** | Before joining league | Scoring rules, participant limits | Players, Referees |
| **games_registry.json** | Referee startup | Game rules, move types, valid choices | Referees |
| **defaults/player.json** | Player initialization | Default strategy, timeout values | Players |
| **defaults/referee.json** | Referee initialization | Default match settings | Referees |

#### 1.A.1 system.json - Global System Settings

**Location:** `SHARED/config/system.json`

**Purpose:** Global parameters for the entire system
**Users:** All agents, Orchestrator

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "system_id": "league_system_prod",
  "protocol_version": "league.v2",
  "last_updated": "2025-01-15T10:00:00Z",

  "network": {
    "league_manager_host": "localhost",
    "league_manager_port": 8000,
    "referee_port_range": [8001, 8010],
    "player_port_range": [8101, 8150]
  },

  "timeouts": {
    "registration_timeout_sec": 10,
    "game_join_timeout_sec": 5,
    "move_timeout_sec": 30,
    "result_notification_timeout_sec": 5,
    "generic_response_timeout_sec": 10
  },

  "retry_policy": {
    "max_retries": 3,
    "base_delay_sec": 2,
    "backoff_strategy": "exponential"
  },

  "security": {
    "token_ttl_hours": 24,
    "require_tls": false
  }
}
```

**How to Use:**
```python
import json
from pathlib import Path

def load_system_config():
    """Load global system configuration."""
    config_path = Path("SHARED/config/system.json")
    with open(config_path) as f:
        return json.load(f)

# Usage in your agent
config = load_system_config()
move_timeout = config["timeouts"]["move_timeout_sec"]  # 30
max_retries = config["retry_policy"]["max_retries"]    # 3
league_port = config["network"]["league_manager_port"] # 8000
```

---

#### 1.A.2 agents_config.json - Agent Registry

**Location:** `SHARED/config/agents/agents_config.json`

**Purpose:** Centralized management of all agents
**Users:** League Manager, Deployment tools

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T10:30:00Z",

  "league_manager": {
    "agent_id": "league_manager",
    "endpoint": "http://localhost:8000/mcp",
    "version": "1.0.0"
  },

  "referees": [
    {
      "referee_id": "REF01",
      "display_name": "Referee Alpha",
      "endpoint": "http://localhost:8001/mcp",
      "game_types": ["even_odd"],
      "max_concurrent_matches": 2
    }
  ],

  "players": [
    {
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "endpoint": "http://localhost:8101/mcp",
      "game_types": ["even_odd"],
      "registered_at": "2025-01-15T09:00:00Z"
    },
    {
      "player_id": "P02",
      "display_name": "Agent Beta",
      "endpoint": "http://localhost:8102/mcp",
      "game_types": ["even_odd"],
      "registered_at": "2025-01-15T09:01:00Z"
    }
  ]
}
```

**When to Update:**
- **League Manager:** After each successful registration (add new agent)
- **Deployment:** During system initialization (load all agents)

---

#### 1.A.3 leagues/\<league_id\>.json - League Configuration

**Location:** `SHARED/config/leagues/league_2025_even_odd.json`

**Purpose:** League-specific settings
**Users:** League Manager, Referees, Players

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "league_id": "league_2025_even_odd",
  "game_type": "even_odd",
  "status": "ACTIVE",
  "created_at": "2025-01-15T08:00:00Z",
  "last_updated": "2025-01-15T10:00:00Z",

  "tournament_format": {
    "type": "round_robin",
    "rounds": "auto"
  },

  "scoring": {
    "win_points": 3,
    "draw_points": 1,
    "loss_points": 0
  },

  "participants": {
    "min_players": 2,
    "max_players": 10000,
    "registration_deadline": "2025-01-15T12:00:00Z"
  },

  "tiebreakers": [
    "head_to_head",
    "win_percentage",
    "total_wins",
    "alphabetical"
  ]
}
```

**How to Use:**
```python
def load_league_config(league_id: str):
    """Load league-specific configuration."""
    config_path = Path(f"SHARED/config/leagues/{league_id}.json")
    with open(config_path) as f:
        return json.load(f)

# Usage
league = load_league_config("league_2025_even_odd")
win_points = league["scoring"]["win_points"]  # 3
max_players = league["participants"]["max_players"]  # 10000
```

---

#### 1.A.4 games_registry.json - Game Types Registry

**Location:** `SHARED/config/games/games_registry.json`

**Purpose:** Registry of all supported game types
**Users:** Referees (for loading rules module), League Manager

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T08:00:00Z",

  "games": {
    "even_odd": {
      "game_type": "even_odd",
      "display_name": "Even/Odd",
      "rules_module": "game_rules.even_odd",
      "move_types": ["choose_parity"],
      "valid_choices": {
        "choose_parity": ["even", "odd"]
      },
      "min_players": 2,
      "max_players": 2,
      "max_round_time_sec": 60,
      "description": "Choose even or odd, referee draws number 1-10"
    },

    "tic_tac_toe": {
      "game_type": "tic_tac_toe",
      "display_name": "Tic-Tac-Toe",
      "rules_module": "game_rules.tic_tac_toe",
      "move_types": ["place_mark"],
      "valid_choices": {
        "place_mark": [0, 1, 2, 3, 4, 5, 6, 7, 8]
      },
      "min_players": 2,
      "max_players": 2,
      "max_round_time_sec": 300
    }
  }
}
```

---

#### 1.A.5 defaults/ - Default Settings

**Location:** `SHARED/config/defaults/`

**Purpose:** Default values by agent type
**Files:** `referee.json`, `player.json`

**defaults/player.json:**
```json
{
  "schema_version": "1.0.0",
  "default_strategy": "random",
  "timeouts": {
    "response_buffer_sec": 2
  },
  "logging": {
    "level": "INFO",
    "log_file": "SHARED/logs/agents/{player_id}.log.jsonl"
  },
  "state_persistence": {
    "enabled": true,
    "save_interval_sec": 60,
    "history_retention_matches": 1000
  }
}
```

**defaults/referee.json:**
```json
{
  "schema_version": "1.0.0",
  "max_concurrent_matches": 2,
  "match_timeout_multiplier": 1.1,
  "logging": {
    "level": "DEBUG",
    "log_file": "SHARED/logs/agents/{referee_id}.log.jsonl"
  }
}
```

---

### 1.B. data/ - Runtime Data Layer

**Purpose:** Dynamic state and historical memory
**When to Use:** To read/write game state, match results, and player history

#### Runtime Data Files Guide

**Table 3: Runtime Data Files Reference**

| File | Who Writes | Who Reads | When to Use |
|------|------------|-----------|-------------|
| **standings.json** | League Manager (after each match) | All players | Check current rankings |
| **rounds.json** | League Manager (after round completion) | Analytics | Review round history |
| **matches/\<match_id\>.json** | Referee (during/after match) | Analytics, Players | Full match transcript |
| **players/\<player_id\>/history.json** | Player (after each match) | Same player | Build strategy from past games |

#### 1.B.1 standings.json - Current League Standings

**Location:** `SHARED/data/leagues/<league_id>/standings.json`

**Purpose:** Real-time tournament rankings
**Updater:** League Manager (after receiving `MATCH_RESULT_REPORT`)

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "league_id": "league_2025_even_odd",
  "version": 12,
  "last_updated": "2025-01-15T11:30:00Z",
  "rounds_completed": 3,

  "standings": [
    {
      "rank": 1,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "games_played": 6,
      "wins": 4,
      "draws": 1,
      "losses": 1,
      "points": 13,
      "win_rate": 0.667
    },
    {
      "rank": 2,
      "player_id": "P03",
      "display_name": "Agent Gamma",
      "games_played": 6,
      "wins": 3,
      "draws": 2,
      "losses": 1,
      "points": 11,
      "win_rate": 0.500
    }
  ]
}
```

**Use Cases:**
- **Players:** Check ranking to adjust strategy (e.g., play risky if low rank)
- **Analytics:** Track player progression over time
- **UI:** Display real-time tournament leaderboard

**How to Use:**
```python
def get_current_standings(league_id: str):
    """Read current standings."""
    standings_path = Path(f"SHARED/data/leagues/{league_id}/standings.json")
    with open(standings_path) as f:
        return json.load(f)

# Usage
standings = get_current_standings("league_2025_even_odd")
my_rank = next(s for s in standings["standings"] if s["player_id"] == "P01")["rank"]
```

---

#### 1.B.2 matches/\<match_id\>.json - Match Transcript

**Location:** `SHARED/data/matches/<league_id>/<match_id>.json`

**Purpose:** Complete documentation of a single match
**Updater:** Referee who managed the match

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "match_id": "R1M1",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "game_type": "even_odd",

  "lifecycle": {
    "created_at": "2025-01-15T10:00:00Z",
    "started_at": "2025-01-15T10:00:10Z",
    "completed_at": "2025-01-15T10:00:45Z",
    "duration_sec": 35,
    "state": "COMPLETED"
  },

  "participants": {
    "player_a": {
      "player_id": "P01",
      "role": "PLAYER_A",
      "response_time_sec": 2.3
    },
    "player_b": {
      "player_id": "P02",
      "role": "PLAYER_B",
      "response_time_sec": 1.8
    }
  },

  "transcript": [
    {
      "timestamp": "2025-01-15T10:00:10Z",
      "event": "GAME_INVITATION_SENT",
      "data": {"player_id": "P01"}
    },
    {
      "timestamp": "2025-01-15T10:00:12Z",
      "event": "GAME_JOIN_ACK_RECEIVED",
      "data": {"player_id": "P01", "accept": true}
    }
  ],

  "result": {
    "status": "WIN",
    "winner_player_id": "P01",
    "drawn_number": 8,
    "number_parity": "even",
    "choices": {
      "P01": "even",
      "P02": "odd"
    },
    "points_awarded": {
      "P01": 3,
      "P02": 0
    },
    "reason": "P01 chose even, number was 8 (even)"
  }
}
```

**Use Cases:**
- **Analytics:** Analyze game patterns and strategies
- **Players:** Review past matches for learning
- **Dispute Resolution:** Complete audit trail of all events
- **Performance Analysis:** Measure response times

---

#### 1.B.3 players/\<player_id\>/history.json - Player Match History

**Location:** `SHARED/data/players/<player_id>/history.json`

**Purpose:** Player's personal match history for strategy building
**Updater:** The player itself (after `notify_match_result`)

**Example Structure:**
```json
{
  "schema_version": "1.0.0",
  "player_id": "P01",
  "last_updated": "2025-01-15T11:30:00Z",

  "stats": {
    "total_matches": 20,
    "wins": 12,
    "losses": 5,
    "draws": 3,
    "total_points": 39,
    "current_streak": {"type": "WIN", "count": 3}
  },

  "matches": [
    {
      "match_id": "R1M1",
      "timestamp": "2025-01-15T10:00:45Z",
      "opponent_id": "P02",
      "result": "WIN",
      "my_choice": "even",
      "opponent_choice": "odd",
      "drawn_number": 8,
      "points_earned": 3
    },
    {
      "match_id": "R1M2",
      "timestamp": "2025-01-15T10:05:20Z",
      "opponent_id": "P03",
      "result": "DRAW",
      "my_choice": "odd",
      "opponent_choice": "odd",
      "drawn_number": 6,
      "points_earned": 1
    }
  ],

  "opponent_profiles": {
    "P02": {
      "matches_played": 3,
      "my_record": {"wins": 2, "losses": 1, "draws": 0},
      "choice_distribution": {"even": 2, "odd": 1},
      "detected_patterns": ["alternating"]
    }
  }
}
```

**Use Cases:**
- **Strategy Development:** Analyze opponent patterns
- **Pattern Detection:** Build statistical models
- **Adaptive Play:** Adjust strategy based on opponent history

**How to Use:**
```python
def get_opponent_history(player_id: str, opponent_id: str):
    """Get match history against specific opponent."""
    history_path = Path(f"SHARED/data/players/{player_id}/history.json")
    with open(history_path) as f:
        history = json.load(f)

    # Filter matches against this opponent
    opponent_matches = [
        m for m in history["matches"]
        if m["opponent_id"] == opponent_id
    ]

    return opponent_matches

# Usage in strategy
opponent_history = get_opponent_history("P01", "P02")
if len(opponent_history) >= 5:
    # Build counter-strategy based on patterns
    opponent_choices = [m["opponent_choice"] for m in opponent_history]
    # Analyze patterns...
```

---

### 1.C. logs/ - Logging Layer

**Purpose:** Tracking and debugging (the "nervous system")
**When to Use:** Continuously during runtime for debugging and monitoring

**Format:** JSON Lines (.jsonl) - one JSON object per line

#### Logging Files Guide

**Table 4: Log Files Reference**

| Log File | Purpose | When to Write | What to Log |
|----------|---------|---------------|-------------|
| **league/\<league_id\>.log.jsonl** | Central league events | League Manager operations | Round announcements, match scheduling |
| **agents/\<agent_id\>.log.jsonl** | Per-agent debugging | Every message sent/received | Invitations, choices, results, errors |
| **system/orchestrator.log.jsonl** | System-level tracking | Orchestrator operations | Agent startups, health checks |

#### 1.C.1 Central League Log

**Location:** `SHARED/logs/league/<league_id>/league.log.jsonl`

**Example Log Entries:**
```jsonl
{"timestamp":"2025-01-15T10:00:00Z","level":"INFO","component":"league_manager","event_type":"ROUND_ANNOUNCEMENT_SENT","round_id":1,"matches_count":2}
{"timestamp":"2025-01-15T10:00:45Z","level":"INFO","component":"league_manager","event_type":"MATCH_RESULT_RECEIVED","match_id":"R1M1","winner":"P01"}
{"timestamp":"2025-01-15T10:05:00Z","level":"INFO","component":"league_manager","event_type":"STANDINGS_UPDATED","version":12}
```

#### 1.C.2 Agent Logs

**Location:** `SHARED/logs/agents/<agent_id>.log.jsonl`

**Example Log Entries (Player):**
```jsonl
{"timestamp":"2025-01-15T10:00:10Z","level":"INFO","agent_id":"P01","message":"Received game invitation","message_type":"GAME_INVITATION","data":{"match_id":"R1M1","opponent":"P02"}}
{"timestamp":"2025-01-15T10:00:12Z","level":"INFO","agent_id":"P01","message":"Sent join acknowledgment","message_type":"GAME_JOIN_ACK","data":{"accept":true}}
{"timestamp":"2025-01-15T10:00:20Z","level":"INFO","agent_id":"P01","message":"Chose parity","message_type":"CHOOSE_PARITY_RESPONSE","data":{"choice":"even","strategy":"adaptive"}}
{"timestamp":"2025-01-15T10:00:45Z","level":"INFO","agent_id":"P01","message":"Match result received","message_type":"GAME_OVER","data":{"result":"WIN","points":3}}
```

**When to Read Logs:**
- **During Development:** Debug why your agent didn't respond
- **After Failures:** Trace exact message sequence that led to timeout
- **Performance Analysis:** Measure response times

**Log Query Examples:**
```bash
# Find all errors for player P01
grep '"level":"ERROR"' SHARED/logs/agents/P01.log.jsonl

# Count total matches for P01
grep '"message_type":"GAME_OVER"' SHARED/logs/agents/P01.log.jsonl | wc -l

# Find timeout events
grep -i timeout SHARED/logs/agents/*.log.jsonl

# Extract all choices made by P01
grep '"message_type":"CHOOSE_PARITY_RESPONSE"' SHARED/logs/agents/P01.log.jsonl | \
  jq -r '.data.choice'
```

---

### 1.D. league_sdk/ - Python SDK

**Purpose:** Shared utilities to avoid writing boilerplate code
**When to Use:** Import instead of reinventing common patterns

#### SDK Modules Guide

**Table 5: SDK Modules Reference**

| Module | What It Provides | When to Use |
|--------|------------------|-------------|
| **config_models.py** | Pydantic models for all configs | Validate config files, type safety |
| **config_loader.py** | ConfigLoader class | Load system.json, league configs easily |
| **repositories.py** | Data access helpers | Read/write standings, match data |
| **logger.py** | JsonLogger class | Structured logging to .jsonl files |

#### Example: Using SDK

```python
# In your agent code
from league_sdk.config_loader import ConfigLoader
from league_sdk.logger import JsonLogger
from league_sdk.repositories import StandingsRepository

# Load system configuration
config = ConfigLoader.load_system_config()
move_timeout = config.timeouts.move_timeout_sec  # 30 (with type safety)

# Initialize structured logger
logger = JsonLogger("P01")
logger.info("Game started", match_id="R1M1")

# Access standings
standings_repo = StandingsRepository("league_2025_even_odd")
current_standings = standings_repo.get_standings()
my_rank = standings_repo.get_player_rank("P01")

# Update player history
from league_sdk.repositories import PlayerHistoryRepository
history_repo = PlayerHistoryRepository("P01")
history_repo.add_match(match_id="R1M1", result="WIN", opponent="P02")
```

---

## 2. agents/ - Agent Implementations

**Purpose:** Where you create your agent code
**When to Use:** Implement your player, referee, or league manager here

### Complete agents/ Structure

```
agents/
├── league_manager/
│   ├── main.py              # Entry point (FastAPI server)
│   ├── handlers.py          # Message handlers (register, report_result)
│   ├── scheduler.py         # Round scheduling logic
│   ├── requirements.txt     # Python dependencies
│   └── README.md            # Agent-specific documentation
│
├── referee_REF01/
│   ├── main.py              # Entry point (FastAPI server)
│   ├── game_logic.py        # Even/Odd rules implementation
│   ├── handlers.py          # Message handlers (start_match, etc.)
│   ├── requirements.txt
│   └── README.md
│
├── player_P01/
│   ├── main.py              # Entry point (FastAPI server)
│   ├── strategy.py          # Playing strategy (random/adaptive/LLM)
│   ├── handlers.py          # Message handlers (3 required tools)
│   ├── requirements.txt
│   └── README.md
│
└── player_P02/
    ├── main.py
    ├── strategy.py
    ├── handlers.py
    ├── requirements.txt
    └── README.md
```

### Typical Agent File Structure

**Table 6: Typical Agent Files**

| File | Purpose | When to Edit |
|------|---------|-------------|
| **main.py** | Entry point – server initialization, config loading | **Always** - First file you create |
| **handlers.py** | Handle incoming messages by type | **Always** - Implement MCP tool handlers |
| **strategy.py** | Decision-making logic *(for players)* | **Players only** - Your game strategy |
| **game_logic.py** | Game rules *(for referees)* | **Referees only** - Winner determination |
| **requirements.txt** | Python dependencies | **As needed** - Add libraries you use |
| **README.md** | Agent documentation | **Recommended** - Document your approach |

---

### 2.1 Building a PLAYER Agent

#### Step-by-Step Player Development

**1. Create Agent Folder**
```bash
mkdir -p agents/player_P01
cd agents/player_P01
```

**2. Create main.py**
```python
# agents/player_P01/main.py
import uvicorn
from fastapi import FastAPI
from league_sdk.config_loader import ConfigLoader
from league_sdk.logger import JsonLogger
from handlers import setup_handlers

# Load configuration
config = ConfigLoader.load_system_config()
player_defaults = ConfigLoader.load_defaults("player")

# Initialize app
app = FastAPI(title="Player P01")
logger = JsonLogger("P01")

# Setup MCP handlers
setup_handlers(app, logger)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "player_id": "P01"}

if __name__ == "__main__":
    # Register with League Manager
    from registration import register_player
    register_player("P01", port=8101)

    # Start server
    uvicorn.run(app, host="0.0.0.0", port=8101)
```

**3. Create handlers.py**
```python
# agents/player_P01/handlers.py
from fastapi import FastAPI
from datetime import datetime, timezone
from strategy import choose_parity_strategy

def setup_handlers(app: FastAPI, logger):
    """Setup MCP tool handlers."""

    @app.post("/mcp")
    async def mcp_endpoint(request: dict):
        method = request.get("method")
        params = request.get("params", {})

        if method == "handle_game_invitation":
            return handle_invitation(params, logger)
        elif method == "choose_parity":
            return choose_parity(params, logger)
        elif method == "notify_match_result":
            return handle_result(params, logger)

        return {"error": "Unknown method"}

def handle_invitation(params, logger):
    """Tool 1: Accept game invitation."""
    logger.info("Received invitation", match_id=params.get("match_id"))

    return {
        "jsonrpc": "2.0",
        "result": {
            "message_type": "GAME_JOIN_ACK",
            "match_id": params.get("match_id"),
            "player_id": "P01",
            "arrival_timestamp": datetime.now(timezone.utc).isoformat(),
            "accept": True
        },
        "id": 1
    }

def choose_parity(params, logger):
    """Tool 2: Choose even or odd."""
    match_id = params.get("match_id")
    opponent_id = params.get("context", {}).get("opponent_id")

    # Use strategy module to make choice
    choice = choose_parity_strategy(opponent_id)

    logger.info("Chose parity", match_id=match_id, choice=choice)

    return {
        "jsonrpc": "2.0",
        "result": {
            "message_type": "CHOOSE_PARITY_RESPONSE",
            "match_id": match_id,
            "player_id": "P01",
            "parity_choice": choice
        },
        "id": 1
    }

def handle_result(params, logger):
    """Tool 3: Store match result."""
    match_id = params.get("match_id")
    result = params.get("game_result", {})

    # Save to player history
    from league_sdk.repositories import PlayerHistoryRepository
    history = PlayerHistoryRepository("P01")
    history.add_match(
        match_id=match_id,
        result=result.get("status"),
        opponent=params.get("opponent_id")
    )

    logger.info("Result stored", match_id=match_id, result=result.get("status"))

    return {
        "jsonrpc": "2.0",
        "result": {"status": "ok"},
        "id": 1
    }
```

**4. Create strategy.py**
```python
# agents/player_P01/strategy.py
import random
from league_sdk.repositories import PlayerHistoryRepository

def choose_parity_strategy(opponent_id: str) -> str:
    """
    Adaptive strategy: analyze opponent history and make informed choice.

    Falls back to random if insufficient data.
    """
    # Load match history
    history = PlayerHistoryRepository("P01")
    opponent_matches = history.get_opponent_matches(opponent_id)

    # Need at least 5 matches for pattern detection
    if len(opponent_matches) < 5:
        return random.choice(["even", "odd"])

    # Analyze opponent's choice distribution
    opponent_choices = [m["opponent_choice"] for m in opponent_matches]
    even_count = opponent_choices.count("even")
    odd_count = opponent_choices.count("odd")

    # If opponent has strong bias (>65%), exploit it
    total = even_count + odd_count
    if total > 0:
        even_ratio = even_count / total
        if even_ratio > 0.65:
            return "even"  # Opponent favors even
        elif even_ratio < 0.35:
            return "odd"   # Opponent favors odd

    # No clear pattern - play random
    return random.choice(["even", "odd"])
```

**5. Create requirements.txt**
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
requests==2.31.0
```

---

### 2.2 Building a REFEREE Agent

**Key Files:**
- **main.py**: Server initialization, load game rules
- **game_logic.py**: Implement `draw_number()`, `determine_winner()`
- **handlers.py**: Implement `start_match`, manage game flow

**game_logic.py Example:**
```python
# agents/referee_REF01/game_logic.py
import secrets

def draw_number() -> int:
    """
    Draw cryptographically secure random number 1-10.

    CRITICAL: Must use secrets module.
    """
    return secrets.randbelow(10) + 1

def determine_winner(choice_a: str, choice_b: str, number: int) -> dict:
    """
    Determine match outcome based on Even/Odd rules.
    """
    is_even = (number % 2 == 0)
    parity = "even" if is_even else "odd"

    # Case 1: Both chose same
    if choice_a == choice_b:
        return {
            "status": "DRAW",
            "winner": None,
            "parity": parity,
            "points": {"player_a": 1, "player_b": 1}
        }

    # Case 2: Different choices
    if choice_a == parity:
        return {
            "status": "WIN",
            "winner": "player_a",
            "parity": parity,
            "points": {"player_a": 3, "player_b": 0}
        }
    else:
        return {
            "status": "WIN",
            "winner": "player_b",
            "parity": parity,
            "points": {"player_a": 0, "player_b": 3}
        }
```

---

### 2.3 Building LEAGUE MANAGER

**Key Files:**
- **main.py**: Server initialization
- **scheduler.py**: Round-robin schedule generation
- **handlers.py**: Implement `register_player`, `report_match_result`, `get_standings`

**scheduler.py Example:**
```python
# agents/league_manager/scheduler.py
from itertools import combinations

def generate_round_robin_schedule(player_ids: list) -> list:
    """
    Generate round-robin schedule.

    Returns:
        List of match dictionaries
    """
    matches = []
    match_num = 1

    for player_a, player_b in combinations(player_ids, 2):
        matches.append({
            "match_id": f"R1M{match_num}",
            "player_A_id": player_a,
            "player_B_id": player_b
        })
        match_num += 1

    return matches
```

---

## 3. doc/ - Documentation

**Purpose:** Reference materials and examples
**When to Use:** During development to verify protocol compliance

### Complete doc/ Structure

```
doc/
├── protocol_spec.md                    # Protocol specification
├── architecture/
│   ├── system_architecture.png
│   └── message_flow_diagram.png
├── message_examples/                   # JSON message examples
│   ├── registration/
│   │   ├── referee_register_request.json
│   │   ├── referee_register_response.json
│   │   ├── player_register_request.json
│   │   └── player_register_response.json
│   ├── game_flow/
│   │   ├── game_invitation.json
│   │   ├── game_join_ack.json
│   │   ├── choose_parity_call.json
│   │   ├── choose_parity_response.json
│   │   └── game_over.json
│   ├── standings/
│   │   └── standings_update.json
│   └── errors/
│       ├── timeout_error.json
│       ├── invalid_move_error.json
│       └── auth_token_error.json
└── api_reference/
    ├── mcp_tools.md
    └── sdk_reference.md
```

### Documentation Resources Table

**Table 7: Documentation Resources**

| Resource | When to Use |
|----------|-------------|
| **protocol_spec.md** | Constantly - Verify message formats |
| **message_examples/registration/** | During registration - Copy exact JSON structure |
| **message_examples/game_flow/** | During game implementation - Validate your messages |
| **message_examples/errors/** | Error handling - Format error responses correctly |
| **architecture/** | Understanding flow - Visualize system architecture |
| **api_reference/** | SDK usage - Learn how to use SDK modules |

---

## 4. Developer Workflows

### 4.1 At Agent Startup

**Checklist:**
- [ ] Read `SHARED/config/system.json` → get timeouts, ports
- [ ] Read `SHARED/config/defaults/<agent_type>.json` → get defaults
- [ ] Initialize `SHARED/logs/agents/<agent_id>.log.jsonl` → start logging
- [ ] Load `SHARED/config/leagues/<league_id>.json` → understand league rules

**Code Example:**
```python
# agents/player_P01/main.py (startup sequence)
from league_sdk.config_loader import ConfigLoader
from league_sdk.logger import JsonLogger

# Step 1: Load system config
system_config = ConfigLoader.load_system_config()
move_timeout = system_config.timeouts.move_timeout_sec

# Step 2: Load player defaults
player_defaults = ConfigLoader.load_defaults("player")
default_strategy = player_defaults.default_strategy

# Step 3: Initialize logger
logger = JsonLogger("P01")
logger.info("Agent starting", version="1.0.0")

# Step 4: Load league config
league_config = ConfigLoader.load_league_config("league_2025_even_odd")
win_points = league_config.scoring.win_points
```

---

### 4.2 During Registration

**Checklist:**
- [ ] Read `SHARED/config/agents/agents_config.json` → check if agent exists
- [ ] Send registration request (copy from `doc/message_examples/registration/`)
- [ ] Log to `SHARED/logs/agents/<agent_id>.log.jsonl`
- [ ] Store auth_token securely (environment variable or config file)

**Code Example:**
```python
import requests
from league_sdk.logger import JsonLogger

def register_player(player_id: str, port: int):
    """Register player with League Manager."""
    logger = JsonLogger(player_id)

    payload = {
        "jsonrpc": "2.0",
        "method": "register_player",
        "params": {
            "player_meta": {
                "display_name": f"Agent {player_id}",
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": f"http://localhost:{port}/mcp"
            }
        },
        "id": 1
    }

    logger.info("Sending registration request")

    response = requests.post(
        "http://localhost:8000/mcp",
        json=payload,
        timeout=10
    )

    result = response.json().get("result", {})

    if result.get("status") == "ACCEPTED":
        auth_token = result["auth_token"]
        # Store token securely
        os.environ[f"{player_id}_AUTH_TOKEN"] = auth_token
        logger.info("Registration successful", player_id=result["player_id"])
    else:
        logger.error("Registration failed", reason=result.get("reason"))
```

---

### 4.3 During Game

**Player Workflow:**
- [ ] Read `SHARED/data/players/<player_id>/history.json` → build strategy
- [ ] Log to `SHARED/logs/agents/<player_id>.log.jsonl` → every message
- [ ] After match: Write to `SHARED/data/players/<player_id>/history.json`

**Referee Workflow:**
- [ ] Write `SHARED/data/matches/<league_id>/<match_id>.json` → save transcript
- [ ] Log to `SHARED/logs/agents/<referee_id>.log.jsonl` → all events
- [ ] After match: Report to League Manager

**Code Example (Player during game):**
```python
def choose_parity(params, logger):
    """Make strategic choice."""
    opponent_id = params.get("context", {}).get("opponent_id")

    # Read history for strategy
    from league_sdk.repositories import PlayerHistoryRepository
    history = PlayerHistoryRepository("P01")
    opponent_matches = history.get_opponent_matches(opponent_id)

    # Log decision
    logger.info("Analyzing opponent",
                opponent_id=opponent_id,
                matches_count=len(opponent_matches))

    # Make choice
    choice = make_strategic_choice(opponent_matches)

    logger.info("Choice made", choice=choice, strategy="adaptive")

    return {"parity_choice": choice}
```

---

### 4.4 After Match

**Player:**
- [ ] Write `SHARED/data/players/<player_id>/history.json` → update history
- [ ] Log final result

**Referee:**
- [ ] Write `SHARED/data/matches/<league_id>/<match_id>.json` → final result
- [ ] Report to League Manager

**League Manager:**
- [ ] Write `SHARED/data/leagues/<league_id>/standings.json` → update rankings
- [ ] Write `SHARED/data/leagues/<league_id>/rounds.json` → if round complete

---

### 4.5 For Debugging

**Checklist:**
- [ ] Read `SHARED/logs/agents/<agent_id>.log.jsonl` → trace messages
- [ ] Read `SHARED/data/matches/<league_id>/<match_id>.json` → review game transcript
- [ ] Check `SHARED/logs/league/<league_id>/league.log.jsonl` → system-level events

**Debug Commands:**
```bash
# Find all errors for agent P01
grep '"level":"ERROR"' SHARED/logs/agents/P01.log.jsonl

# Trace specific match
grep '"match_id":"R1M1"' SHARED/logs/agents/*.log.jsonl

# Check timeout events
grep -i timeout SHARED/logs/agents/P01.log.jsonl

# Review match transcript
cat SHARED/data/matches/league_2025_even_odd/R1M1.json | jq '.transcript'

# Check standings
cat SHARED/data/leagues/league_2025_even_odd/standings.json | jq '.standings'
```

---

## 5. Quick Reference Guide

### 5.1 When to Use What

**Table 8: Quick Reference - File Usage by Scenario**

| Scenario | Files to Access | Action |
|----------|----------------|--------|
| **Agent Startup** | `config/system.json`, `config/defaults/<type>.json` | READ configs |
| **Registration** | `config/agents/agents_config.json` | READ to check, WRITE after success |
| **Before Match** | `data/players/<id>/history.json`, `data/leagues/<id>/standings.json` | READ for strategy |
| **During Match** | `logs/agents/<id>.log.jsonl` | WRITE every message |
| **After Match** | `data/players/<id>/history.json`, `data/matches/<id>/<match>.json` | WRITE results |
| **Debugging** | `logs/agents/<id>.log.jsonl`, `data/matches/<id>/<match>.json` | READ logs and transcripts |

---

### 5.2 Common File Access Patterns

**Pattern 1: Load Configuration**
```python
from league_sdk.config_loader import ConfigLoader

config = ConfigLoader.load_system_config()
league = ConfigLoader.load_league_config("league_2025_even_odd")
defaults = ConfigLoader.load_defaults("player")
```

**Pattern 2: Log Structured Events**
```python
from league_sdk.logger import JsonLogger

logger = JsonLogger("P01")
logger.info("Event occurred", match_id="R1M1", data={"key": "value"})
logger.error("Error occurred", error_code="E001")
```

**Pattern 3: Read/Write Player History**
```python
from league_sdk.repositories import PlayerHistoryRepository

history = PlayerHistoryRepository("P01")

# Read
opponent_matches = history.get_opponent_matches("P02")
total_wins = history.get_total_wins()

# Write
history.add_match(match_id="R1M1", result="WIN", opponent="P02")
```

**Pattern 4: Update Standings**
```python
from league_sdk.repositories import StandingsRepository

standings = StandingsRepository("league_2025_even_odd")

# Read
current = standings.get_standings()
my_rank = standings.get_player_rank("P01")

# Write (League Manager only)
standings.update_after_match(match_result)
```

---

## 6. Best Practices

### 6.1 File Access Best Practices

**DO:**
- ✅ Use SDK repositories instead of direct file access
- ✅ Validate file schema before processing
- ✅ Use atomic writes for data files (SDK handles this)
- ✅ Log all file access (success and failure)
- ✅ Handle file not found gracefully

**DON'T:**
- ❌ Modify files without schema validation
- ❌ Write directly to files (bypassing SDK)
- ❌ Cache file contents indefinitely (configs may update)
- ❌ Ignore file access errors
- ❌ Hard-code file paths (use SDK path helpers)

---

### 6.2 Logging Best Practices

**DO:**
- ✅ Log every incoming message
- ✅ Log every outgoing message
- ✅ Include `match_id` and `conversation_id` in logs
- ✅ Use structured logging (JSON Lines)
- ✅ Log at appropriate levels (DEBUG/INFO/WARN/ERROR)

**DON'T:**
- ❌ Log sensitive data (auth tokens)
- ❌ Log to stdout (use .jsonl files)
- ❌ Skip logging errors
- ❌ Use unstructured log messages
- ❌ Log without timestamps

---

### 6.3 Data Management Best Practices

**DO:**
- ✅ Validate data against schema before saving
- ✅ Include `last_updated` timestamp
- ✅ Use atomic writes (SDK handles this)
- ✅ Back up before major changes
- ✅ Implement data retention policies

**DON'T:**
- ❌ Modify data files manually (use SDK)
- ❌ Save without schema version
- ❌ Skip validation
- ❌ Store unbounded history (implement limits)
- ❌ Ignore data corruption errors

---

## 7. Common Scenarios

### Scenario 1: New Player Joins Tournament

**Files Accessed:**
1. **READ** `config/system.json` → get League Manager port
2. **READ** `config/defaults/player.json` → get default settings
3. **WRITE** `config/agents/agents_config.json` → add player to registry
4. **WRITE** `logs/agents/P01.log.jsonl` → log registration
5. **CREATE** `data/players/P01/history.json` → initialize history

---

### Scenario 2: Player Makes Strategic Decision

**Files Accessed:**
1. **READ** `data/players/P01/history.json` → get opponent history
2. **READ** `data/leagues/league_2025_even_odd/standings.json` → check current rank
3. **WRITE** `logs/agents/P01.log.jsonl` → log decision process
4. **RETURN** choice to referee

---

### Scenario 3: Match Completes

**Files Accessed:**
1. **WRITE** `data/matches/league_2025_even_odd/R1M1.json` → save full transcript (Referee)
2. **WRITE** `data/players/P01/history.json` → update player history (Player)
3. **WRITE** `data/players/P02/history.json` → update player history (Player)
4. **WRITE** `data/leagues/league_2025_even_odd/standings.json` → update standings (League Manager)
5. **WRITE** `logs/league/league_2025_even_odd/league.log.jsonl` → log result (League Manager)

---

### Scenario 4: Debugging Timeout Error

**Files Accessed:**
1. **READ** `logs/agents/P01.log.jsonl` → find timeout event
2. **READ** `data/matches/league_2025_even_odd/R1M1.json` → review match transcript
3. **READ** `logs/league/league_2025_even_odd/league.log.jsonl` → check system events
4. **ANALYZE** response times in logs
5. **FIX** code, test again

---

## 8. Troubleshooting

### Common Issues & Solutions

**Issue 1: File Not Found**
```
FileNotFoundError: SHARED/config/system.json
```

**Solution:**
- Verify you're running from project root directory
- Check SHARED/ folder exists
- Use SDK path helpers: `ConfigLoader.get_config_path("system.json")`

---

**Issue 2: Schema Validation Failed**
```
ValidationError: 'schema_version' is required
```

**Solution:**
- Ensure all files include required fields:
  - `schema_version`
  - `last_updated`
  - `id` (for primary objects)
- Use SDK models for automatic validation

---

**Issue 3: Permission Denied**
```
PermissionError: [Errno 13] Permission denied: 'SHARED/data/...'
```

**Solution:**
- Check file permissions: `chmod 644 SHARED/data/**/*.json`
- Ensure agent has write access to `data/` and `logs/`
- Run with appropriate user permissions

---

**Issue 4: Logs Not Appearing**
```
# No logs written to file
```

**Solution:**
- Check logger initialization: `logger = JsonLogger("P01")`
- Verify log directory exists: `mkdir -p SHARED/logs/agents`
- Ensure logger writes to correct file
- Check log level (DEBUG vs INFO)

---

**Issue 5: Standings Not Updating**
```
# Standings show old data
```

**Solution:**
- Verify League Manager received `MATCH_RESULT_REPORT`
- Check League Manager logs for errors
- Ensure atomic write completed successfully
- Refresh standings cache (don't cache indefinitely)

---

## 9. Summary

### Key Takeaways

**1. Three-Layer Organization:**
- **SHARED/** = Shared resources (configs, data, logs, SDK)
- **agents/** = Your agent implementations
- **doc/** = Reference materials

**2. File Access Patterns:**
- **READ** configs at startup
- **READ/WRITE** data during runtime
- **WRITE** logs continuously
- **REFERENCE** docs during development

**3. Best Practices:**
- Use SDK instead of direct file access
- Validate all data against schemas
- Log everything with structured format
- Follow atomic write patterns
- Implement data retention policies

**4. Developer Workflow:**
- Start with `doc/` to understand protocol
- Use SDK for common tasks
- Implement in `agents/<your_agent>/`
- Test with local SHARED/ resources
- Debug with logs and transcripts

---

**Questions? See:**
- `three-layer-architecture-requirements.md` (detailed architecture)
- `developer-implementation-guide.md` (implementation patterns)
- `game-protocol-messages-prd.md` (all message formats)

**Good luck organizing your project! 📂🚀**
