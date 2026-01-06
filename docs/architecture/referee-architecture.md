# Referee Architecture (Game Orchestrator)

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
4. [Game State Machine](#4-game-state-machine)
5. [6-Phase Game Flow](#5-6-phase-game-flow)
6. [Simultaneous Move Collection](#6-simultaneous-move-collection)
7. [Winner Determination](#7-winner-determination)
8. [Implementation Template](#8-implementation-template)

---

## 1. Introduction

The **Referee** is the game orchestrator responsible for managing individual Even/Odd matches. Each referee can handle 1-2 concurrent matches.

### 1.1 Agent Role

```
┌──────────────────────────────────────────┐
│        REFEREE (Ports 8001-8010)         │
├──────────────────────────────────────────┤
│  MCP Server (FastAPI)                    │
│  - Receives match assignments            │
│  - Manages game lifecycle                │
├──────────────────────────────────────────┤
│  Game Orchestrator                       │
│  - Send invitations                      │
│  - Collect choices (simultaneous)        │
│  - Draw number (cryptographic random)    │
│  - Determine winner                      │
│  - Report to League Manager              │
├──────────────────────────────────────────┤
│  State Machine                           │
│  - WAITING_FOR_PLAYERS                   │
│  - COLLECTING_CHOICES                    │
│  - DRAWING_NUMBER                        │
│  - EVALUATING                            │
│  - FINISHED                              │
└──────────────────────────────────────────┘
```

---

## 2. Responsibilities

| Responsibility | Description | Priority |
|----------------|-------------|----------|
| **Register with League** | Send REFEREE_REGISTER_REQUEST on startup | CRITICAL |
| **Receive Match Assignments** | Accept match assignments from League Manager | CRITICAL |
| **Send Invitations** | Invite both players to match | CRITICAL |
| **Collect Choices** | Get parity choice from each player (simultaneous) | CRITICAL |
| **Draw Number** | Generate cryptographically random number 1-10 | CRITICAL |
| **Determine Winner** | Compare choices to number parity | CRITICAL |
| **Report Result** | Send MATCH_RESULT_REPORT to League Manager | CRITICAL |
| **Timeout Enforcement** | Enforce 5s and 30s timeouts with retry | HIGH |
| **Error Recovery** | Handle player disconnections gracefully | HIGH |

---

## 3. Component Architecture

### 3.1 Directory Structure

```
agents/referee_REF01/
├── main.py                  # Entry point, MCP server
├── config.py                # Configuration
├── game_orchestrator.py     # Main game loop
├── handlers/
│   ├── __init__.py
│   └── match_assignment.py  # Receive match assignments
├── game_logic/
│   ├── __init__.py
│   ├── state_machine.py     # Game state transitions
│   ├── number_generator.py  # Cryptographic random
│   └── winner_evaluator.py  # Determine winner
├── storage/
│   ├── __init__.py
│   └── match_store.py       # Active match state
└── utils/
    ├── __init__.py
    └── logger.py            # JSON logging
```

---

## 4. Game State Machine

### 4.1 State Diagram

```
                    START
                      ↓
          ┌───────────────────────┐
          │ WAITING_FOR_PLAYERS   │
          └───────────────────────┘
                      ↓ (both players accepted)
          ┌───────────────────────┐
          │ COLLECTING_CHOICES    │
          └───────────────────────┘
                      ↓ (both choices received)
          ┌───────────────────────┐
          │  DRAWING_NUMBER       │
          └───────────────────────┘
                      ↓
          ┌───────────────────────┐
          │    EVALUATING         │
          └───────────────────────┘
                      ↓
          ┌───────────────────────┐
          │     FINISHED          │
          └───────────────────────┘
                      ↓
                    END

     Timeout/Error → ABORTED (from any state)
```

### 4.2 State Implementation

```python
from enum import Enum

class GameState(Enum):
    """Game state machine states."""
    WAITING_FOR_PLAYERS = "waiting_for_players"
    COLLECTING_CHOICES = "collecting_choices"
    DRAWING_NUMBER = "drawing_number"
    EVALUATING = "evaluating"
    FINISHED = "finished"
    ABORTED = "aborted"

class GameStateMachine:
    """Manages game state transitions."""

    # Valid transitions
    TRANSITIONS = {
        GameState.WAITING_FOR_PLAYERS: {GameState.COLLECTING_CHOICES, GameState.ABORTED},
        GameState.COLLECTING_CHOICES: {GameState.DRAWING_NUMBER, GameState.ABORTED},
        GameState.DRAWING_NUMBER: {GameState.EVALUATING},
        GameState.EVALUATING: {GameState.FINISHED},
        GameState.FINISHED: set(),
        GameState.ABORTED: set()
    }

    def __init__(self, match_id: str):
        self.match_id = match_id
        self.state = GameState.WAITING_FOR_PLAYERS
        self.history = [(self.state, datetime.now())]

    def transition(self, new_state: GameState):
        """Transition to new state with validation."""
        if new_state not in self.TRANSITIONS[self.state]:
            raise ValueError(
                f"Invalid transition: {self.state} → {new_state}"
            )

        logger.info(
            "State transition",
            match_id=self.match_id,
            from_state=self.state.value,
            to_state=new_state.value
        )

        self.state = new_state
        self.history.append((self.state, datetime.now()))

    def can_transition(self, new_state: GameState) -> bool:
        """Check if transition is valid."""
        return new_state in self.TRANSITIONS[self.state]
```

---

## 5. 6-Phase Game Flow

### 5.1 Phase 1: Registration

**When:** On referee startup

```python
async def register_to_league():
    """Register with League Manager."""
    response = await mcp_client.call_tool(
        endpoint="http://localhost:8000/mcp",
        method="register_referee",
        params={
            "protocol": "league.v2",
            "message_type": "REFEREE_REGISTER_REQUEST",
            "sender": "referee:alpha",
            "timestamp": get_utc_timestamp(),
            "conversation_id": "convrefalphareg001",
            "referee_meta": {
                "display_name": "Referee Alpha",
                "version": "1.0.0",
                "game_types": ["even_odd"],
                "contact_endpoint": f"http://localhost:{config.port}/mcp",
                "max_concurrent_matches": 2
            }
        }
    )

    result = response["result"]
    config.set_credentials(
        referee_id=result["referee_id"],
        auth_token=result["auth_token"],
        league_id=result["league_id"]
    )
```

### 5.2 Phase 2: Match Assignment

**Received from:** League Manager

```python
async def handle_match_assignment(params: dict) -> dict:
    """
    Receive match assignment from League Manager.

    Params:
        - match_id
        - player_A_id
        - player_B_id
        - player_A_endpoint
        - player_B_endpoint
    """
    match_id = params["match_id"]

    # Create game state
    game = GameStateMachine(match_id)
    match_store.add_game(match_id, game)

    # Start game orchestration (async)
    asyncio.create_task(orchestrate_game(params))

    return {"status": "accepted", "match_id": match_id}
```

### 5.3 Phase 3: Player Invitations

**State:** WAITING_FOR_PLAYERS

```python
async def send_invitations(match_params: dict):
    """Send GAME_INVITATION to both players."""
    match_id = match_params["match_id"]
    game = match_store.get_game(match_id)

    # Send invitations in parallel
    invitation_params_A = {
        "protocol": "league.v2",
        "message_type": "GAME_INVITATION",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}001",
        "auth_token": config.auth_token,
        "league_id": config.league_id,
        "round_id": match_params["round_id"],
        "match_id": match_id,
        "game_type": "even_odd",
        "role_in_match": "PLAYER_A",
        "opponent_id": match_params["player_B_id"]
    }

    invitation_params_B = {**invitation_params_A}
    invitation_params_B["role_in_match"] = "PLAYER_B"
    invitation_params_B["opponent_id"] = match_params["player_A_id"]

    # Call both players concurrently (with timeout)
    results = await asyncio.gather(
        call_with_retry(
            mcp_client.call_tool,
            RetryConfig(max_retries=3),
            endpoint=match_params["player_A_endpoint"],
            method="handle_game_invitation",
            params=invitation_params_A
        ),
        call_with_retry(
            mcp_client.call_tool,
            RetryConfig(max_retries=3),
            endpoint=match_params["player_B_endpoint"],
            method="handle_game_invitation",
            params=invitation_params_B
        ),
        return_exceptions=True
    )

    # Check both accepted
    for i, result in enumerate(results):
        if isinstance(result, Exception) or not result.get("result", {}).get("accept"):
            game.transition(GameState.ABORTED)
            await report_aborted_game(match_id, f"Player {i+1} no-show")
            return False

    # Proceed to next phase
    game.transition(GameState.COLLECTING_CHOICES)
    return True
```

### 5.4 Phase 4: Collect Choices (CRITICAL - Simultaneous)

**State:** COLLECTING_CHOICES

```python
async def collect_choices(match_params: dict):
    """
    Collect parity choices from both players SIMULTANEOUSLY.

    CRITICAL: Choices must be collected without revealing to each other.
    """
    match_id = match_params["match_id"]
    game = match_store.get_game(match_id)

    choice_params_base = {
        "protocol": "league.v2",
        "message_type": "CHOOSE_PARITY_CALL",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}001",
        "auth_token": config.auth_token,
        "match_id": match_id,
        "game_type": "even_odd",
        "deadline": (datetime.now(timezone.utc) + timedelta(seconds=30)).strftime("%Y%m%dT%H%M%SZ")
    }

    # Prepare params for each player
    choice_params_A = {**choice_params_base}
    choice_params_A["player_id"] = match_params["player_A_id"]
    choice_params_A["context"] = {
        "opponent_id": match_params["player_B_id"],
        "round_id": match_params["round_id"]
    }

    choice_params_B = {**choice_params_base}
    choice_params_B["player_id"] = match_params["player_B_id"]
    choice_params_B["context"] = {
        "opponent_id": match_params["player_A_id"],
        "round_id": match_params["round_id"]
    }

    # Call both players SIMULTANEOUSLY (critical for fairness)
    results = await asyncio.gather(
        call_with_retry(
            mcp_client.call_tool,
            RetryConfig(max_retries=3),
            endpoint=match_params["player_A_endpoint"],
            method="choose_parity",
            params=choice_params_A
        ),
        call_with_retry(
            mcp_client.call_tool,
            RetryConfig(max_retries=3),
            endpoint=match_params["player_B_endpoint"],
            method="choose_parity",
            params=choice_params_B
        ),
        return_exceptions=True
    )

    # Extract choices
    choices = {}
    for i, result in enumerate(results):
        player_id = match_params[f"player_{'A' if i == 0 else 'B'}_id"]

        if isinstance(result, Exception):
            # Timeout or error - award technical loss
            game.transition(GameState.ABORTED)
            await report_aborted_game(match_id, f"{player_id} timeout")
            return None

        choice = result["result"]["parity_choice"]

        # Validate choice
        if choice not in ["even", "odd"]:
            game.transition(GameState.ABORTED)
            await report_aborted_game(match_id, f"{player_id} invalid choice")
            return None

        choices[player_id] = choice

    game.transition(GameState.DRAWING_NUMBER)
    return choices
```

### 5.5 Phase 5: Draw Number and Evaluate

**States:** DRAWING_NUMBER → EVALUATING

```python
import secrets

async def draw_and_evaluate(match_params: dict, choices: dict):
    """Draw number and determine winner."""
    match_id = match_params["match_id"]
    game = match_store.get_game(match_id)

    # Draw number (1-10) using cryptographic randomness
    drawn_number = secrets.randbelow(10) + 1

    # Determine parity
    number_parity = "even" if drawn_number % 2 == 0 else "odd"

    game.transition(GameState.EVALUATING)

    # Determine winner
    player_A_id = match_params["player_A_id"]
    player_B_id = match_params["player_B_id"]

    if choices[player_A_id] == number_parity:
        winner_id = player_A_id
    elif choices[player_B_id] == number_parity:
        winner_id = player_B_id
    else:
        # Both wrong (impossible in this game)
        winner_id = None

    game.transition(GameState.FINISHED)

    result = {
        "status": "WIN" if winner_id else "DRAW",
        "winner_player_id": winner_id,
        "drawn_number": drawn_number,
        "number_parity": number_parity,
        "choices": choices,
        "reason": f"{winner_id} chose {choices[winner_id]}, number was {drawn_number} ({number_parity})"
    }

    return result
```

### 5.6 Phase 6: Notify and Report

**State:** FINISHED

```python
async def send_game_over_and_report(match_params: dict, result: dict):
    """Send GAME_OVER to players and report to League Manager."""
    match_id = match_params["match_id"]

    # Send GAME_OVER to both players
    game_over_params = {
        "protocol": "league.v2",
        "message_type": "GAME_OVER",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}001",
        "auth_token": config.auth_token,
        "match_id": match_id,
        "game_type": "even_odd",
        "game_result": result
    }

    # Notify players (fire-and-forget, no need to wait)
    await asyncio.gather(
        mcp_client.call_tool(
            endpoint=match_params["player_A_endpoint"],
            method="notify_match_result",
            params=game_over_params
        ),
        mcp_client.call_tool(
            endpoint=match_params["player_B_endpoint"],
            method="notify_match_result",
            params=game_over_params
        ),
        return_exceptions=True
    )

    # Report to League Manager
    report_params = {
        "protocol": "league.v2",
        "message_type": "MATCH_RESULT_REPORT",
        "sender": f"referee:{config.referee_id}",
        "timestamp": get_utc_timestamp(),
        "conversation_id": f"conv{match_id}report",
        "auth_token": config.auth_token,
        "league_id": config.league_id,
        "round_id": match_params["round_id"],
        "match_id": match_id,
        "game_type": "even_odd",
        "result": {
            "winner": result["winner_player_id"],
            "score": {
                match_params["player_A_id"]: 3 if result["winner_player_id"] == match_params["player_A_id"] else 0,
                match_params["player_B_id"]: 3 if result["winner_player_id"] == match_params["player_B_id"] else 0
            },
            "details": {
                "drawn_number": result["drawn_number"],
                "choices": result["choices"]
            }
        }
    }

    await mcp_client.call_tool(
        endpoint="http://localhost:8000/mcp",
        method="report_match_result",
        params=report_params
    )

    logger.info("Match completed and reported", match_id=match_id, winner=result["winner_player_id"])
```

---

## 6. Simultaneous Move Collection

### 6.1 Why Simultaneous?

**Problem:** If we collect choices sequentially, the second player could have an advantage (knowing the first player responded).

**Solution:** Use `asyncio.gather()` to call both players **at the exact same time**.

### 6.2 Implementation

```python
# CORRECT: Simultaneous collection
results = await asyncio.gather(
    call_player_A(),
    call_player_B()
)

# WRONG: Sequential collection
result_A = await call_player_A()  # Player B could observe timing
result_B = await call_player_B()  # Player B knows A already responded
```

---

## 7. Winner Determination

### 7.1 Game Rules

**Drawn Number → Parity:**
- 1, 3, 5, 7, 9 → "odd"
- 2, 4, 6, 8, 10 → "even"

**Winner:**
- Player who chose the matching parity wins
- Other player loses
- (No draws possible in this game)

### 7.2 Implementation

```python
def determine_winner(drawn_number: int, choices: dict) -> dict:
    """
    Determine match winner.

    Args:
        drawn_number: Random number 1-10
        choices: {player_id: "even" or "odd"}

    Returns:
        Result dict with winner, scores, details
    """
    # Determine parity
    number_parity = "even" if drawn_number % 2 == 0 else "odd"

    # Find winner
    winner_id = None
    for player_id, choice in choices.items():
        if choice == number_parity:
            winner_id = player_id
            break

    # Calculate scores
    scores = {}
    for player_id in choices.keys():
        scores[player_id] = 3 if player_id == winner_id else 0

    return {
        "status": "WIN",
        "winner_player_id": winner_id,
        "drawn_number": drawn_number,
        "number_parity": number_parity,
        "choices": choices,
        "scores": scores
    }
```

---

## 8. Implementation Template

### 8.1 Complete game_orchestrator.py

```python
"""
Game Orchestrator - Main game loop for a single match.
"""

import asyncio
from datetime import datetime, timezone, timedelta
from game_logic.state_machine import GameStateMachine, GameState
from game_logic.number_generator import draw_number
from game_logic.winner_evaluator import determine_winner
from common.mcp_client import MCPClient
from common.retry import call_with_retry, RetryConfig

async def orchestrate_game(match_params: dict):
    """
    Orchestrate a complete game from invitation to result reporting.

    Params:
        match_id, round_id, player_A_id, player_B_id,
        player_A_endpoint, player_B_endpoint
    """
    match_id = match_params["match_id"]
    logger.info("Starting game orchestration", match_id=match_id)

    # Create game state
    game = GameStateMachine(match_id)

    try:
        # Phase 1: Send invitations
        success = await send_invitations(match_params, game)
        if not success:
            return

        # Phase 2: Collect choices (simultaneous)
        choices = await collect_choices(match_params, game)
        if not choices:
            return

        # Phase 3: Draw and evaluate
        result = await draw_and_evaluate(match_params, game, choices)

        # Phase 4: Notify and report
        await send_game_over_and_report(match_params, result)

        logger.info("Game completed successfully", match_id=match_id)

    except Exception as e:
        logger.error(f"Game orchestration failed: {str(e)}", match_id=match_id)
        game.transition(GameState.ABORTED)
        await report_aborted_game(match_id, str(e))
```

---

## Summary

The Referee architecture provides:

✅ **6-Phase Game Flow** (registration → invitation → choice → draw → evaluate → report)
✅ **Game State Machine** with validated transitions
✅ **Simultaneous Move Collection** for fairness
✅ **Cryptographic Random Number** generation
✅ **Timeout Enforcement** with retry logic
✅ **Complete Implementation Template**

**Next Steps:**
1. Implement game_orchestrator.py
2. Implement state machine
3. Test with mock players
4. Deploy and register with League Manager

---

**Related Documents:**
- [common-design.md](./common-design.md) - MCP server patterns
- [player-agent-architecture.md](./player-agent-architecture.md) - Player interface
- [league-manager-architecture.md](./league-manager-architecture.md) - Match assignment

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
