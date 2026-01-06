# League Manager Architecture

**Document Type:** Agent Architecture
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** System Developers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Responsibilities](#2-responsibilities)
3. [Component Architecture](#3-component-architecture)
4. [Registration System](#4-registration-system)
5. [Round-Robin Scheduling](#5-round-robin-scheduling)
6. [Standings Calculation](#6-standings-calculation)
7. [Round Management](#7-round-management)
8. [Implementation Template](#8-implementation-template)

---

## 1. Introduction

The **League Manager** is the top-level orchestrator for the Even/Odd tournament. It manages all agent registrations, creates the tournament schedule, tracks standings, and coordinates rounds.

### 1.1 Agent Role

```
┌──────────────────────────────────────────┐
│     LEAGUE MANAGER (Port 8000)           │
├──────────────────────────────────────────┤
│  MCP Server (FastAPI)                    │
│  - register_referee                      │
│  - register_player                       │
│  - report_match_result                   │
│  - league_query (standings)              │
├──────────────────────────────────────────┤
│  Registration System                     │
│  - Token generation                      │
│  - Agent registry (players, referees)    │
│  - Capacity management                   │
├──────────────────────────────────────────┤
│  Scheduler                               │
│  - Round-robin algorithm                 │
│  - Referee assignment                    │
│  - Match dispatching                     │
├──────────────────────────────────────────┤
│  Standings Tracker                       │
│  - Point calculation (W=3, T=1, L=0)     │
│  - Tiebreaker logic                      │
│  - Broadcast updates                     │
├──────────────────────────────────────────┤
│  Round Coordinator                       │
│  - Round announcements                   │
│  - Match completion tracking             │
│  - Round completion detection            │
└──────────────────────────────────────────┘
```

### 1.2 Source of Truth

The League Manager is the **single source of truth** for:
- Agent registry (all players and referees)
- Tournament schedule (all matches)
- Current standings (points, wins, losses, ties)
- Round status (pending, active, completed)

---

## 2. Responsibilities

| Responsibility | Description | Priority |
|----------------|-------------|----------|
| **Referee Registration** | Accept referee registrations, assign IDs and tokens | CRITICAL |
| **Player Registration** | Accept player registrations, assign IDs and tokens | CRITICAL |
| **Schedule Creation** | Generate round-robin schedule for all players | CRITICAL |
| **Match Assignment** | Assign matches to referees | HIGH |
| **Standings Tracking** | Calculate and update standings after each match | CRITICAL |
| **Round Management** | Announce rounds, track completion | HIGH |
| **League Completion** | Declare champion, finalize tournament | MEDIUM |
| **Query Handling** | Respond to standings queries | MEDIUM |

---

## 3. Component Architecture

### 3.1 Directory Structure

```
agents/league_manager/
├── main.py                  # Entry point, MCP server
├── config.py                # Configuration
├── handlers/
│   ├── __init__.py
│   ├── referee_registration.py
│   ├── player_registration.py
│   ├── match_result.py
│   └── league_query.py
├── scheduler/
│   ├── __init__.py
│   ├── round_robin.py       # Round-robin algorithm
│   └── referee_assigner.py  # Assign referees to matches
├── standings/
│   ├── __init__.py
│   ├── calculator.py        # Calculate standings
│   └── tiebreaker.py        # Tiebreaker logic
├── registry/
│   ├── __init__.py
│   ├── agent_registry.py    # Store all agents
│   └── token_store.py       # Auth tokens
└── utils/
    ├── __init__.py
    └── logger.py            # JSON logging
```

---

## 4. Registration System

### 4.1 Referee Registration

**Handler:** `register_referee`

**Request:**
```json
{
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
}
```

**Implementation:**
```python
from registry.agent_registry import AgentRegistry
from registry.token_store import TokenStore
from authentication import generate_auth_token

async def register_referee(params: dict) -> dict:
    """Register a referee and assign ID + token."""
    referee_meta = params["referee_meta"]

    # Generate referee_id (sequential: REF01, REF02, ...)
    referee_id = f"REF{len(agent_registry.get_referees()) + 1:02d}"

    # Generate auth token
    auth_token = generate_auth_token("referee", referee_id)

    # Store referee
    agent_registry.add_referee(
        referee_id=referee_id,
        display_name=referee_meta["display_name"],
        endpoint=referee_meta["contact_endpoint"],
        game_types=referee_meta["game_types"],
        max_concurrent_matches=referee_meta["max_concurrent_matches"],
        version=referee_meta["version"]
    )

    # Store token
    token_store.store_referee_token(referee_id, auth_token)

    logger.info(
        "Referee registered",
        referee_id=referee_id,
        display_name=referee_meta["display_name"]
    )

    return {
        "protocol": "league.v2",
        "message_type": "REFEREE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": get_utc_timestamp(),
        "conversation_id": params["conversation_id"],
        "status": "ACCEPTED",
        "referee_id": referee_id,
        "auth_token": auth_token,
        "league_id": config.league_id
    }
```

### 4.2 Player Registration

**Handler:** `register_player`

**Implementation:**
```python
async def register_player(params: dict) -> dict:
    """Register a player and assign ID + token."""
    player_meta = params["player_meta"]

    # Check capacity
    if len(agent_registry.get_players()) >= config.max_players:
        return {
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_RESPONSE",
            "status": "REJECTED",
            "reason": "League full"
        }

    # Generate player_id (sequential: P01, P02, ...)
    player_id = f"P{len(agent_registry.get_players()) + 1:02d}"

    # Generate auth token
    auth_token = generate_auth_token("player", player_id)

    # Store player
    agent_registry.add_player(
        player_id=player_id,
        display_name=player_meta["display_name"],
        endpoint=player_meta["contact_endpoint"],
        game_types=player_meta["game_types"],
        version=player_meta["version"]
    )

    # Store token
    token_store.store_player_token(player_id, auth_token)

    # Initialize standings
    standings_tracker.add_player(player_id, player_meta["display_name"])

    logger.info(
        "Player registered",
        player_id=player_id,
        display_name=player_meta["display_name"]
    )

    return {
        "protocol": "league.v2",
        "message_type": "LEAGUE_REGISTER_RESPONSE",
        "sender": "league_manager",
        "timestamp": get_utc_timestamp(),
        "conversation_id": params["conversation_id"],
        "status": "ACCEPTED",
        "player_id": player_id,
        "auth_token": auth_token,
        "league_id": config.league_id
    }
```

---

## 5. Round-Robin Scheduling

### 5.1 Algorithm

For **N players**, generate matches where:
- Every player plays every other player exactly once
- Total matches: `N * (N-1) / 2`
- Distributed evenly across rounds

**Example (4 players):**
- Round 1: P01 vs P02, P03 vs P04
- Round 2: P01 vs P03, P02 vs P04
- Round 3: P01 vs P04, P02 vs P03
- **Total:** 6 matches

### 5.2 Implementation

```python
from itertools import combinations

def create_round_robin_schedule(player_ids: list) -> list:
    """
    Create round-robin schedule for all players.

    Args:
        player_ids: List of player IDs

    Returns:
        List of rounds, each round is list of matches
    """
    # Generate all possible pairings
    all_matches = list(combinations(player_ids, 2))

    # Distribute matches across rounds (simple approach)
    num_rounds = len(player_ids) - 1 if len(player_ids) % 2 == 0 else len(player_ids)
    rounds = [[] for _ in range(num_rounds)]

    # Assign matches to rounds (ensuring no player plays twice in same round)
    round_idx = 0
    for match in all_matches:
        # Find round where neither player is already playing
        for i in range(num_rounds):
            players_in_round = set()
            for m in rounds[i]:
                players_in_round.add(m[0])
                players_in_round.add(m[1])

            if match[0] not in players_in_round and match[1] not in players_in_round:
                rounds[i].append(match)
                break

    return rounds

# Usage
player_ids = ["P01", "P02", "P03", "P04"]
rounds = create_round_robin_schedule(player_ids)

# Output:
# [
#   [("P01", "P02"), ("P03", "P04")],  # Round 1
#   [("P01", "P03"), ("P02", "P04")],  # Round 2
#   [("P01", "P04"), ("P02", "P03")]   # Round 3
# ]
```

### 5.3 Referee Assignment

```python
def assign_referees_to_matches(schedule: list, referees: list) -> list:
    """
    Assign referees to matches.

    Simple round-robin assignment of referees.
    """
    referee_idx = 0
    assigned_schedule = []

    for round_matches in schedule:
        round_data = []
        for match in round_matches:
            # Assign next available referee
            referee = referees[referee_idx % len(referees)]
            referee_idx += 1

            round_data.append({
                "player_A_id": match[0],
                "player_B_id": match[1],
                "referee_id": referee["referee_id"],
                "referee_endpoint": referee["endpoint"]
            })

        assigned_schedule.append(round_data)

    return assigned_schedule
```

---

## 6. Standings Calculation

### 6.1 Scoring Rules

| Result | Points |
|--------|--------|
| Win    | 3      |
| Tie    | 1      |
| Loss   | 0      |

### 6.2 Tiebreaker Order

1. **Total Points** (descending)
2. **Head-to-Head Result** (if only 2 players tied)
3. **Alphabetical by player_id** (fallback)

### 6.3 Implementation

```python
class StandingsCalculator:
    """Calculate and maintain tournament standings."""

    def __init__(self):
        self.players = {}  # player_id → stats

    def add_player(self, player_id: str, display_name: str):
        """Initialize player stats."""
        self.players[player_id] = {
            "player_id": player_id,
            "display_name": display_name,
            "played": 0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "points": 0
        }

    def record_match(self, player_A_id: str, player_B_id: str, winner_id: str):
        """Record match result and update standings."""
        self.players[player_A_id]["played"] += 1
        self.players[player_B_id]["played"] += 1

        if winner_id == player_A_id:
            # A wins, B loses
            self.players[player_A_id]["wins"] += 1
            self.players[player_A_id]["points"] += 3
            self.players[player_B_id]["losses"] += 1
        elif winner_id == player_B_id:
            # B wins, A loses
            self.players[player_B_id]["wins"] += 1
            self.players[player_B_id]["points"] += 3
            self.players[player_A_id]["losses"] += 1
        else:
            # Draw (not possible in Even/Odd, but handle generically)
            self.players[player_A_id]["draws"] += 1
            self.players[player_A_id]["points"] += 1
            self.players[player_B_id]["draws"] += 1
            self.players[player_B_id]["points"] += 1

    def get_standings(self) -> list:
        """
        Get current standings (sorted).

        Returns:
            List of player stats sorted by rank
        """
        standings = list(self.players.values())

        # Sort by points (desc), then alphabetically
        standings.sort(key=lambda p: (-p["points"], p["player_id"]))

        # Assign ranks
        for i, player in enumerate(standings):
            player["rank"] = i + 1

        return standings
```

### 6.4 Broadcasting Standings

```python
async def broadcast_standings_update(round_id: int):
    """Send LEAGUE_STANDINGS_UPDATE to all players."""
    standings = standings_calculator.get_standings()

    message = {
        "protocol": "league.v2",
        "message_type": "LEAGUE_STANDINGS_UPDATE",
        "sender": "league_manager",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"convround{round_id}standings",
        "league_id": config.league_id,
        "round_id": round_id,
        "standings": standings
    }

    # Send to all players (fire-and-forget)
    players = agent_registry.get_players()
    tasks = []
    for player in players:
        task = mcp_client.call_tool(
            endpoint=player["endpoint"],
            method="update_standings",
            params=message
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Standings update broadcast", round_id=round_id)
```

---

## 7. Round Management

### 7.1 Round States

```
PENDING → ANNOUNCED → IN_PROGRESS → COMPLETED
```

### 7.2 Round Announcement

```python
async def announce_round(round_id: int):
    """
    Announce round to all players.

    Then, assign matches to referees.
    """
    round_matches = schedule[round_id - 1]

    # Create ROUND_ANNOUNCEMENT message
    announcement = {
        "protocol": "league.v2",
        "message_type": "ROUND_ANNOUNCEMENT",
        "sender": "league_manager",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"convround{round_id}announce",
        "league_id": config.league_id,
        "round_id": round_id,
        "matches": [
            {
                "match_id": f"R{round_id}M{i+1}",
                "game_type": "even_odd",
                "player_A_id": match["player_A_id"],
                "player_B_id": match["player_B_id"],
                "referee_endpoint": match["referee_endpoint"]
            }
            for i, match in enumerate(round_matches)
        ]
    }

    # Broadcast to all players
    players = agent_registry.get_players()
    tasks = []
    for player in players:
        task = mcp_client.call_tool(
            endpoint=player["endpoint"],
            method="notify_round",
            params=announcement
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    # Assign matches to referees
    for i, match in enumerate(round_matches):
        await assign_match_to_referee(round_id, i+1, match)

    logger.info("Round announced", round_id=round_id, matches=len(round_matches))
```

### 7.3 Match Result Handling

```python
async def handle_match_result(params: dict) -> dict:
    """
    Handle MATCH_RESULT_REPORT from referee.

    Update standings and check if round is complete.
    """
    round_id = params["round_id"]
    match_id = params["match_id"]
    result = params["result"]

    # Record match result
    standings_calculator.record_match(
        player_A_id=result["score"].keys()[0],
        player_B_id=result["score"].keys()[1],
        winner_id=result["winner"]
    )

    # Mark match as complete
    match_tracker.mark_complete(match_id)

    logger.info("Match result recorded", match_id=match_id, winner=result["winner"])

    # Check if round is complete
    if match_tracker.is_round_complete(round_id):
        await finalize_round(round_id)

    return {"status": "recorded"}
```

### 7.4 Round Completion

```python
async def finalize_round(round_id: int):
    """
    Finalize round after all matches complete.

    1. Broadcast standings update
    2. Send ROUND_COMPLETED notification
    3. Check if league is complete
    """
    # Broadcast standings
    await broadcast_standings_update(round_id)

    # Send ROUND_COMPLETED
    completion = {
        "protocol": "league.v2",
        "message_type": "ROUND_COMPLETED",
        "sender": "league_manager",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"convround{round_id}complete",
        "league_id": config.league_id,
        "round_id": round_id,
        "matches_played": len(schedule[round_id - 1]),
        "next_round_id": round_id + 1 if round_id < len(schedule) else None
    }

    # Broadcast to all players
    players = agent_registry.get_players()
    tasks = []
    for player in players:
        task = mcp_client.call_tool(
            endpoint=player["endpoint"],
            method="notify_round_completed",
            params=completion
        )
        tasks.append(task)

    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("Round completed", round_id=round_id)

    # Check if league is complete
    if round_id == len(schedule):
        await finalize_league()
    else:
        # Announce next round
        await announce_round(round_id + 1)
```

---

## 8. Implementation Template

### 8.1 Complete main.py

```python
"""
League Manager - Top-level tournament orchestrator
"""

import asyncio
from common.mcp_server import MCPServer
from common.logger import JsonLogger
from config import Config

# Import handlers
from handlers.referee_registration import register_referee
from handlers.player_registration import register_player
from handlers.match_result import handle_match_result
from handlers.league_query import handle_league_query

# Import components
from registry.agent_registry import AgentRegistry
from registry.token_store import TokenStore
from scheduler.round_robin import create_round_robin_schedule
from standings.calculator import StandingsCalculator

# Initialize
config = Config()
logger = JsonLogger("league_manager")
agent_registry = AgentRegistry()
token_store = TokenStore()
standings_calculator = StandingsCalculator()

# Create MCP server
server = MCPServer("league_manager", port=8000)

# Register tools
server.register_tool("register_referee", register_referee)
server.register_tool("register_player", register_player)
server.register_tool("report_match_result", handle_match_result)
server.register_tool("league_query", handle_league_query)

async def start_league():
    """
    Start the league after all registrations are complete.

    Called manually by admin.
    """
    players = agent_registry.get_players()
    referees = agent_registry.get_referees()

    logger.info(
        "Starting league",
        num_players=len(players),
        num_referees=len(referees)
    )

    # Create schedule
    player_ids = [p["player_id"] for p in players]
    schedule = create_round_robin_schedule(player_ids)

    # Assign referees
    assigned_schedule = assign_referees_to_matches(schedule, referees)

    # Store schedule
    config.set_schedule(assigned_schedule)

    # Announce first round
    await announce_round(round_id=1)

def main():
    """Main entry point."""
    logger.info("League Manager starting on port 8000")
    server.run()

if __name__ == "__main__":
    main()
```

---

## Summary

The League Manager architecture provides:

✅ **Registration System** for referees and players with token generation
✅ **Round-Robin Scheduling** for fair tournament structure
✅ **Standings Calculation** with tiebreaker logic
✅ **Round Management** (announcement → completion)
✅ **Broadcast Patterns** for notifying all agents
✅ **Complete Implementation Template**

**Next Steps:**
1. Implement agent registry and token store
2. Implement round-robin scheduler
3. Implement standings calculator
4. Test with mock agents
5. Deploy and start accepting registrations

---

**Related Documents:**
- [common-design.md](./common-design.md) - MCP server patterns
- [authentication-design.md](./authentication-design.md) - Token generation
- [referee-architecture.md](./referee-architecture.md) - Match assignment interface
- [player-agent-architecture.md](./player-agent-architecture.md) - Registration interface

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
