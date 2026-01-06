# Player Agent Architecture

**Document Type:** Agent Architecture
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** Student Developers (YOUR MAIN TASK)

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Responsibilities](#2-responsibilities)
3. [Component Architecture](#3-component-architecture)
4. [Required MCP Tools](#4-required-mcp-tools)
5. [Strategy Engine](#5-strategy-engine)
6. [Game History Storage](#6-game-history-storage)
7. [Implementation Template](#7-implementation-template)
8. [Testing Strategy](#8-testing-strategy)

---

## 1. Introduction

The **Player Agent** is an autonomous AI agent that participates in Even/Odd game tournaments. It's implemented as an MCP server exposing 3 required tools.

### 1.1 Agent Role

```
┌──────────────────────────────────────────┐
│         PLAYER AGENT (Port 8101+)        │
├──────────────────────────────────────────┤
│  MCP Server (FastAPI)                    │
│  ├─ handle_game_invitation (5s timeout)  │
│  ├─ choose_parity (30s timeout)          │
│  └─ notify_match_result                  │
├──────────────────────────────────────────┤
│  Strategy Engine (Pluggable)             │
│  ├─ Random Strategy                      │
│  ├─ Adaptive Strategy                    │
│  └─ LLM Strategy (Optional)              │
├──────────────────────────────────────────┤
│  Game History Storage                    │
│  └─ Match records, opponent profiles     │
└──────────────────────────────────────────┘
```

### 1.2 Success Criteria

**Minimum Viable Player (Week 1):**
- ✅ Responds to all 3 MCP tools correctly
- ✅ Completes within timeout constraints
- ✅ Implements random strategy (50/50 baseline)
- ✅ Participates in full tournament without crashes

**Competitive Player (Week 2+):**
- ✅ Implements adaptive strategy with pattern detection
- ✅ Learns from opponent history
- ✅ Win rate > 50% against patterned opponents

---

## 2. Responsibilities

### 2.1 Core Responsibilities

| Responsibility | Description | Priority |
|----------------|-------------|----------|
| **Accept Invitations** | Respond to GAME_INVITATION within 5 seconds | CRITICAL |
| **Make Choices** | Return "even" or "odd" within 30 seconds | CRITICAL |
| **Store Results** | Record match outcomes for learning | HIGH |
| **Implement Strategy** | Choose parity based on opponent patterns | MEDIUM |
| **Handle Errors** | Gracefully handle timeouts and failures | HIGH |

### 2.2 Communication Patterns

**Receives messages from:**
- Referee: `GAME_INVITATION`, `CHOOSE_PARITY_CALL`, `GAME_OVER`
- League Manager: `ROUND_ANNOUNCEMENT`, `LEAGUE_STANDINGS_UPDATE`, `LEAGUE_COMPLETED`

**Sends messages to:**
- League Manager: `LEAGUE_REGISTER_REQUEST`
- Referee: `GAME_JOIN_ACK`, `CHOOSE_PARITY_RESPONSE`

---

## 3. Component Architecture

### 3.1 Directory Structure

```
agents/player_P01/
├── main.py                  # Entry point, MCP server setup
├── config.py                # Configuration management
├── handlers/
│   ├── __init__.py
│   ├── invitation.py        # handle_game_invitation
│   ├── choice.py            # choose_parity
│   └── result.py            # notify_match_result
├── strategies/
│   ├── __init__.py
│   ├── base.py              # Strategy interface
│   ├── random_strategy.py   # Random 50/50
│   ├── adaptive_strategy.py # Pattern detection
│   └── llm_strategy.py      # LLM-based (optional)
├── storage/
│   ├── __init__.py
│   ├── history.py           # Match history storage
│   └── opponent_profiler.py # Opponent pattern analysis
└── utils/
    ├── __init__.py
    └── logger.py            # JSON logging
```

### 3.2 Component Diagram

```
┌─────────────────────────────────────────────────────┐
│                   main.py                           │
│             (MCP Server Setup)                      │
└─────────────────┬───────────────────────────────────┘
                  │
      ┌───────────┼───────────┐
      ↓           ↓           ↓
┌──────────┐ ┌─────────┐ ┌──────────┐
│invitation│ │ choice  │ │  result  │ (handlers/)
└────┬─────┘ └────┬────┘ └────┬─────┘
     │            │            │
     │       ┌────┴────┐       │
     │       ↓         ↓       │
     │  ┌─────────┐ ┌─────────┐│
     │  │ Random  │ │Adaptive ││ (strategies/)
     │  │Strategy │ │Strategy ││
     │  └─────────┘ └─────────┘│
     │                          │
     └──────────┬───────────────┘
                ↓
         ┌──────────────┐
         │   storage/   │
         │  - history   │
         │  - profiler  │
         └──────────────┘
```

---

## 4. Required MCP Tools

### 4.1 Tool 1: handle_game_invitation

**Purpose:** Accept or reject game invitations from referee

**Timeout:** 5 seconds (CRITICAL)

**Request Schema:**
```python
{
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
}
```

**Response Schema:**
```python
{
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
}
```

**Implementation:**
```python
from datetime import datetime, timezone
from timeout import with_timeout

@with_timeout(5)  # CRITICAL: Must respond within 5 seconds
async def handle_game_invitation(params: dict) -> dict:
    """
    Handle game invitation from referee.

    Args:
        params: GAME_INVITATION message

    Returns:
        GAME_JOIN_ACK response
    """
    logger.info(
        "Game invitation received",
        conversation_id=params["conversation_id"],
        match_id=params["match_id"],
        opponent_id=params["opponent_id"]
    )

    # Always accept invitations (required for tournament)
    return {
        "protocol": "league.v2",
        "message_type": "GAME_JOIN_ACK",
        "sender": f"player:{config.player_id}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params["conversation_id"],
        "auth_token": config.auth_token,
        "match_id": params["match_id"],
        "player_id": config.player_id,
        "arrival_timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "accept": True
    }
```

---

### 4.2 Tool 2: choose_parity

**Purpose:** Choose "even" or "odd" based on strategy

**Timeout:** 30 seconds (CRITICAL)

**Request Schema:**
```python
{
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
}
```

**Response Schema:**
```python
{
  "protocol": "league.v2",
  "message_type": "CHOOSE_PARITY_RESPONSE",
  "sender": "player:P01",
  "timestamp": "20250115T10:15:10Z",
  "conversation_id": "convr1m1001",
  "auth_token": "tok_p01_xyz789",
  "match_id": "R1M1",
  "player_id": "P01",
  "parity_choice": "even"  # MUST be "even" or "odd"
}
```

**Implementation:**
```python
from timeout import with_timeout
from strategies import StrategyFactory

@with_timeout(30)  # CRITICAL: Must respond within 30 seconds
async def choose_parity(params: dict) -> dict:
    """
    Choose parity based on current strategy.

    Args:
        params: CHOOSE_PARITY_CALL message

    Returns:
        CHOOSE_PARITY_RESPONSE with "even" or "odd"
    """
    match_id = params["match_id"]
    opponent_id = params["context"]["opponent_id"]

    logger.info(
        "Parity choice requested",
        conversation_id=params["conversation_id"],
        match_id=match_id,
        opponent_id=opponent_id
    )

    # Get strategy (configured in config.py)
    strategy = StrategyFactory.get_strategy(config.strategy_type)

    # Get opponent history
    opponent_history = history_store.get_opponent_matches(opponent_id)

    # Get current standings (from params)
    standings = params["context"].get("your_standings", {})

    # Make choice
    choice = strategy.choose_parity(
        match_id=match_id,
        opponent_id=opponent_id,
        opponent_history=opponent_history,
        standings=standings
    )

    # Validate choice
    if choice not in ["even", "odd"]:
        logger.error(f"Invalid choice: {choice}, defaulting to 'even'")
        choice = "even"

    logger.info(
        "Parity choice made",
        conversation_id=params["conversation_id"],
        choice=choice,
        strategy=config.strategy_type
    )

    return {
        "protocol": "league.v2",
        "message_type": "CHOOSE_PARITY_RESPONSE",
        "sender": f"player:{config.player_id}",
        "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
        "conversation_id": params["conversation_id"],
        "auth_token": config.auth_token,
        "match_id": match_id,
        "player_id": config.player_id,
        "parity_choice": choice
    }
```

---

### 4.3 Tool 3: notify_match_result

**Purpose:** Receive and store match results for learning

**Timeout:** None (fire-and-forget notification)

**Request Schema:**
```python
{
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
}
```

**Response Schema:**
```python
{
  "acknowledged": true
}
```

**Implementation:**
```python
async def notify_match_result(params: dict) -> dict:
    """
    Store match result for learning.

    Args:
        params: GAME_OVER message

    Returns:
        Acknowledgment
    """
    match_id = params["match_id"]
    result = params["game_result"]

    logger.info(
        "Match result received",
        conversation_id=params["conversation_id"],
        match_id=match_id,
        winner=result["winner_player_id"],
        drawn_number=result["drawn_number"]
    )

    # Determine opponent
    opponent_id = None
    for player_id in result["choices"].keys():
        if player_id != config.player_id:
            opponent_id = player_id
            break

    # Store match record
    match_record = {
        "match_id": match_id,
        "opponent_id": opponent_id,
        "my_choice": result["choices"][config.player_id],
        "opponent_choice": result["choices"][opponent_id],
        "drawn_number": result["drawn_number"],
        "number_parity": result["number_parity"],
        "won": result["winner_player_id"] == config.player_id,
        "timestamp": params["timestamp"]
    }

    history_store.add_match(match_record)

    # Update opponent profile for adaptive strategy
    opponent_profiler.update_profile(
        opponent_id=opponent_id,
        choice=result["choices"][opponent_id]
    )

    logger.info(
        "Match result stored",
        match_id=match_id,
        total_matches=history_store.get_total_matches()
    )

    return {"acknowledged": True}
```

---

## 5. Strategy Engine

### 5.1 Strategy Interface

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class Strategy(ABC):
    """Base class for all strategies."""

    @abstractmethod
    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """
        Choose parity for this match.

        Args:
            match_id: Current match ID
            opponent_id: Opponent player ID
            opponent_history: Past matches against this opponent
            standings: Current tournament standings

        Returns:
            "even" or "odd"
        """
        pass
```

### 5.2 Random Strategy (Baseline)

```python
import random

class RandomStrategy(Strategy):
    """
    Random 50/50 strategy (baseline).

    This is the minimum viable strategy. Against other random
    players, win rate will be ~50%.
    """

    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """Choose randomly between even and odd."""
        return random.choice(["even", "odd"])
```

### 5.3 Adaptive Strategy (Pattern Detection)

```python
from collections import Counter
from scipy.stats import chisquare

class AdaptiveStrategy(Strategy):
    """
    Adaptive strategy with pattern detection.

    Logic:
    1. Detect if opponent has pattern (chi-squared test)
    2. If pattern detected, exploit it
    3. If no pattern, play random
    """

    def __init__(self, min_samples: int = 5, significance: float = 0.05):
        self.min_samples = min_samples
        self.significance = significance

    def choose_parity(
        self,
        match_id: str,
        opponent_id: str,
        opponent_history: List[Dict],
        standings: Dict
    ) -> str:
        """Choose based on opponent pattern detection."""

        # Not enough data - play random
        if len(opponent_history) < self.min_samples:
            return random.choice(["even", "odd"])

        # Extract opponent choices
        opponent_choices = [m["opponent_choice"] for m in opponent_history]

        # Count frequencies
        counts = Counter(opponent_choices)
        even_freq = counts.get("even", 0) / len(opponent_choices)
        odd_freq = counts.get("odd", 0) / len(opponent_choices)

        # Chi-squared test for pattern
        observed = [counts.get("even", 0), counts.get("odd", 0)]
        expected = [len(opponent_choices) / 2, len(opponent_choices) / 2]

        _, p_value = chisquare(observed, expected)

        # Pattern detected (reject null hypothesis of 50/50)
        if p_value < self.significance:
            # Exploit: if opponent favors even, we choose odd
            if even_freq > odd_freq:
                return "odd"  # Counter opponent's bias
            else:
                return "even"

        # No pattern detected - play random
        return random.choice(["even", "odd"])
```

### 5.4 Strategy Factory

```python
class StrategyFactory:
    """Factory for creating strategy instances."""

    _strategies = {
        "random": RandomStrategy,
        "adaptive": AdaptiveStrategy
    }

    _current_strategy = None

    @classmethod
    def get_strategy(cls, strategy_type: str) -> Strategy:
        """Get strategy instance (singleton)."""
        if cls._current_strategy is None:
            strategy_class = cls._strategies.get(strategy_type, RandomStrategy)
            cls._current_strategy = strategy_class()
        return cls._current_strategy

    @classmethod
    def set_strategy(cls, strategy_type: str):
        """Change strategy (for testing)."""
        strategy_class = cls._strategies.get(strategy_type, RandomStrategy)
        cls._current_strategy = strategy_class()
```

---

## 6. Game History Storage

### 6.1 History Store Implementation

```python
import json
from pathlib import Path
from typing import List, Dict

class HistoryStore:
    """Persistent storage for match history."""

    def __init__(self, player_id: str, data_dir: str = "SHARED/data/players"):
        self.player_id = player_id
        self.file_path = Path(data_dir) / player_id / "match_history.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.matches = self._load()

    def _load(self) -> List[Dict]:
        """Load match history from file."""
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return []

    def _save(self):
        """Save match history to file (atomic write)."""
        temp_path = self.file_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(self.matches, f, indent=2)
        temp_path.replace(self.file_path)

    def add_match(self, match_record: Dict):
        """Add a match record."""
        self.matches.append(match_record)
        self._save()

    def get_opponent_matches(self, opponent_id: str) -> List[Dict]:
        """Get all matches against a specific opponent."""
        return [m for m in self.matches if m["opponent_id"] == opponent_id]

    def get_total_matches(self) -> int:
        """Get total number of matches played."""
        return len(self.matches)

    def get_win_rate(self) -> float:
        """Calculate overall win rate."""
        if not self.matches:
            return 0.0
        wins = sum(1 for m in self.matches if m["won"])
        return wins / len(self.matches)
```

### 6.2 Opponent Profiler

```python
class OpponentProfiler:
    """Track opponent patterns for adaptive strategy."""

    def __init__(self, player_id: str, data_dir: str = "SHARED/data/players"):
        self.player_id = player_id
        self.file_path = Path(data_dir) / player_id / "opponent_profiles.json"
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.profiles = self._load()

    def _load(self) -> Dict:
        """Load opponent profiles."""
        if self.file_path.exists():
            with open(self.file_path, 'r') as f:
                return json.load(f)
        return {}

    def _save(self):
        """Save profiles (atomic write)."""
        temp_path = self.file_path.with_suffix('.tmp')
        with open(temp_path, 'w') as f:
            json.dump(self.profiles, f, indent=2)
        temp_path.replace(self.file_path)

    def update_profile(self, opponent_id: str, choice: str):
        """Update opponent profile with new choice."""
        if opponent_id not in self.profiles:
            self.profiles[opponent_id] = {
                "total_matches": 0,
                "even_count": 0,
                "odd_count": 0
            }

        profile = self.profiles[opponent_id]
        profile["total_matches"] += 1
        if choice == "even":
            profile["even_count"] += 1
        else:
            profile["odd_count"] += 1

        # Calculate frequencies
        profile["even_frequency"] = profile["even_count"] / profile["total_matches"]
        profile["odd_frequency"] = profile["odd_count"] / profile["total_matches"]

        self._save()

    def get_profile(self, opponent_id: str) -> Dict:
        """Get opponent profile."""
        return self.profiles.get(opponent_id, {})
```

---

## 7. Implementation Template

### 7.1 Complete main.py

```python
"""
Player Agent - Even/Odd Game League
Main entry point
"""

import asyncio
from pathlib import Path

# Import MCP server components
from common.mcp_server import MCPServer
from common.logger import JsonLogger
from config import Config

# Import handlers
from handlers.invitation import handle_game_invitation
from handlers.choice import choose_parity
from handlers.result import notify_match_result

# Import storage
from storage.history import HistoryStore
from storage.opponent_profiler import OpponentProfiler

# Initialize configuration
config = Config()

# Initialize logger
logger = JsonLogger(
    agent_id=config.player_id or "P_UNREGISTERED",
    log_file=f"SHARED/logs/agents/{config.player_id or 'temp'}.log.jsonl"
)

# Initialize storage
history_store = HistoryStore(player_id=config.player_id or "temp")
opponent_profiler = OpponentProfiler(player_id=config.player_id or "temp")

# Create MCP server
server = MCPServer(
    agent_id=config.player_id or "P_UNREGISTERED",
    port=config.port
)

# Register tools
server.register_tool("handle_game_invitation", handle_game_invitation)
server.register_tool("choose_parity", choose_parity)
server.register_tool("notify_match_result", notify_match_result)

async def register_to_league():
    """Register with League Manager."""
    from common.mcp_client import MCPClient
    from datetime import datetime, timezone

    client = MCPClient(timeout=10)

    response = await client.call_tool(
        endpoint="http://localhost:8000/mcp",
        method="register_player",
        params={
            "protocol": "league.v2",
            "message_type": "LEAGUE_REGISTER_REQUEST",
            "sender": f"player:{config.temp_name}",
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "conversation_id": f"conv{config.temp_name}reg001",
            "player_meta": {
                "display_name": config.display_name,
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": f"http://localhost:{config.port}/mcp"
            }
        }
    )

    result = response["result"]

    # Store credentials
    config.set_credentials(
        player_id=result["player_id"],
        auth_token=result["auth_token"],
        league_id=result["league_id"]
    )

    logger.info(
        "Registration successful",
        player_id=config.player_id,
        league_id=config.league_id
    )

    await client.close()

def main():
    """Main entry point."""
    logger.info("Player Agent starting", port=config.port)

    # Register with league (if not already registered)
    if not config.player_id:
        asyncio.run(register_to_league())

    # Start MCP server
    server.run()

if __name__ == "__main__":
    main()
```

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# tests/test_random_strategy.py
import pytest
from strategies.random_strategy import RandomStrategy

def test_random_strategy_returns_valid_choice():
    strategy = RandomStrategy()
    choice = strategy.choose_parity("M1", "P02", [], {})
    assert choice in ["even", "odd"]

def test_random_strategy_roughly_50_50():
    strategy = RandomStrategy()
    choices = [strategy.choose_parity("M1", "P02", [], {}) for _ in range(1000)]
    even_count = choices.count("even")
    assert 400 < even_count < 600  # Roughly 50/50
```

### 8.2 Integration Tests

```python
# tests/integration/test_player_flow.py
import pytest
from mcp_client import MCPClient

@pytest.mark.asyncio
async def test_complete_game_flow():
    client = MCPClient()

    # 1. Send invitation
    response = await client.call_tool(
        endpoint="http://localhost:8101/mcp",
        method="handle_game_invitation",
        params={...}
    )
    assert response["result"]["accept"] == True

    # 2. Request choice
    response = await client.call_tool(
        endpoint="http://localhost:8101/mcp",
        method="choose_parity",
        params={...}
    )
    assert response["result"]["parity_choice"] in ["even", "odd"]
```

---

## Summary

The Player Agent architecture provides:

✅ **3 Required MCP Tools** with timeout enforcement
✅ **Pluggable Strategy Engine** (Random, Adaptive, LLM)
✅ **Game History Storage** for learning
✅ **Opponent Profiling** for pattern detection
✅ **Complete Implementation Template**
✅ **Testing Strategy** for validation

**Next Steps:**
1. Implement `main.py` using the template
2. Implement Random Strategy first (baseline)
3. Add Adaptive Strategy (pattern detection)
4. Test with mock referee
5. Deploy to tournament

---

**Related Documents:**
- [common-design.md](./common-design.md) - MCP server patterns
- [message-envelope-design.md](./message-envelope-design.md) - Message structure
- [authentication-design.md](./authentication-design.md) - Registration flow

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
