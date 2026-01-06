# Game Flow Logic Design

**Document Type:** Architecture Design
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** All Developers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Complete Game Flow Overview](#2-complete-game-flow-overview)
3. [Phase-by-Phase Flow](#3-phase-by-phase-flow)
4. [State Transitions](#4-state-transitions)
5. [Message Sequence Diagrams](#5-message-sequence-diagrams)
6. [Timeout Handling](#6-timeout-handling)
7. [Error Scenarios](#7-error-scenarios)
8. [Success Criteria](#8-success-criteria)

---

## 1. Introduction

This document describes the **complete flow of a single Even/Odd game** from tournament start to match completion. It covers all message exchanges between League Manager, Referee, and Players.

### 1.1 Participating Agents

```
┌─────────────────┐
│ League Manager  │ (Port 8000) - Orchestrates tournament
└────────┬────────┘
         │
    ┌────┴────┐
    ↓         ↓
┌─────────┐ ┌─────────┐
│Referee  │ │Referee  │ (Ports 8001-8010) - Manage individual games
└────┬────┘ └────┬────┘
     │           │
  ┌──┴──┐     ┌──┴──┐
  ↓     ↓     ↓     ↓
┌───┐ ┌───┐ ┌───┐ ┌───┐
│P01│ │P02│ │P03│ │P04│ (Ports 8101+) - Play games
└───┘ └───┘ └───┘ └───┘
```

---

## 2. Complete Game Flow Overview

### 2.1 High-Level Flow

```
┌──────────────────────────────────────────────────────────────┐
│                   TOURNAMENT START                           │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  PHASE 1: REGISTRATION                                       │
│  - Referees register with League Manager                     │
│  - Players register with League Manager                      │
│  - Receive player_id/referee_id + auth_token                 │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  PHASE 2: SCHEDULING                                         │
│  - League Manager creates round-robin schedule               │
│  - Assigns referees to matches                               │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  PHASE 3: ROUND ANNOUNCEMENT                                 │
│  - League Manager sends ROUND_ANNOUNCEMENT to all players    │
│  - Players become aware of their matches                     │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  PHASE 4: MATCH ORCHESTRATION (For Each Match)               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4.1: Invitations    (Referee → Players)               │  │
│  │      - GAME_INVITATION                                 │  │
│  │      - GAME_JOIN_ACK                                   │  │
│  │      - Timeout: 5 seconds                              │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4.2: Choice Collection (Referee → Players)            │  │
│  │      - CHOOSE_PARITY_CALL                              │  │
│  │      - CHOOSE_PARITY_RESPONSE                          │  │
│  │      - Timeout: 30 seconds                             │  │
│  │      - CRITICAL: Simultaneous collection               │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4.3: Number Drawing   (Referee internal)              │  │
│  │      - Draw random number 1-10 (cryptographic)         │  │
│  │      - Determine parity (even/odd)                     │  │
│  │      - Calculate winner                                │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4.4: Result Notification (Referee → Players)          │  │
│  │      - GAME_OVER                                       │  │
│  │      - Players update internal state                   │  │
│  └────────────────────────────────────────────────────────┘  │
│                           ↓                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 4.5: Result Reporting (Referee → League Manager)      │  │
│  │      - MATCH_RESULT_REPORT                             │  │
│  │      - League Manager updates standings                │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
                           ↓
┌──────────────────────────────────────────────────────────────┐
│  PHASE 5: ROUND COMPLETION                                   │
│  - All matches in round complete                             │
│  - League Manager broadcasts LEAGUE_STANDINGS_UPDATE         │
│  - League Manager sends ROUND_COMPLETED                      │
└──────────────────────────────────────────────────────────────┘
                           ↓
             ┌─────────────────────────┐
             │ More Rounds?            │
             └─────────────────────────┘
                  Yes ↓         ↓ No
         (Loop to PHASE 3)      ↓
                           ┌──────────────────────────┐
                           │ PHASE 6: LEAGUE COMPLETE │
                           │ - Declare champion       │
                           │ - Archive results        │
                           └──────────────────────────┘
```

---

## 3. Phase-by-Phase Flow

### 3.1 Phase 1: Registration

**Timeline:** Before tournament starts

**Actors:** Referees, Players, League Manager

**Flow:**

```
Referee REF01                League Manager
     |                              |
     | REFEREE_REGISTER_REQUEST     |
     |----------------------------->|
     |                              | (Generate referee_id, auth_token)
     | REFEREE_REGISTER_RESPONSE    |
     |<-----------------------------|
     |   referee_id: REF01          |
     |   auth_token: tok_ref01_...  |
     |                              |

Player P01                   League Manager
     |                              |
     | LEAGUE_REGISTER_REQUEST      |
     |----------------------------->|
     |                              | (Generate player_id, auth_token)
     | LEAGUE_REGISTER_RESPONSE     |
     |<-----------------------------|
     |   player_id: P01             |
     |   auth_token: tok_p01_...    |
     |                              |
```

**State Changes:**
- League Manager: Stores referee/player in registry
- League Manager: Generates and stores auth tokens
- Referee/Player: Stores credentials locally

**Critical Timing:** No timeout (blocking until registration complete)

---

### 3.2 Phase 2: Scheduling

**Timeline:** After all registrations, before first round

**Actors:** League Manager (internal)

**Algorithm:**
1. Retrieve all registered players
2. Generate round-robin pairings (N*(N-1)/2 matches)
3. Distribute matches across rounds (no player plays twice in same round)
4. Assign referees to matches (round-robin or by capacity)

**Example (4 players):**
```python
# Input: ["P01", "P02", "P03", "P04"]
# Output:
Round 1: [("P01", "P02"), ("P03", "P04")]  → Assign to REF01
Round 2: [("P01", "P03"), ("P02", "P04")]  → Assign to REF01
Round 3: [("P01", "P04"), ("P02", "P03")]  → Assign to REF01
```

**State Changes:**
- League Manager: Creates and stores complete schedule
- League Manager: Marks round 1 as "PENDING"

---

### 3.3 Phase 3: Round Announcement

**Timeline:** Start of each round

**Actors:** League Manager, All Players

**Flow:**

```
League Manager              Player P01              Player P02 ... P04
     |                          |                        |
     | ROUND_ANNOUNCEMENT       |                        |
     |------------------------->|----------------------->|
     |  round_id: 1             |                        |
     |  matches: [R1M1, R1M2]   |                        |
     |                          |                        |
     |                    (Players log announcement)     |
```

**Message Content:**
```json
{
  "message_type": "ROUND_ANNOUNCEMENT",
  "round_id": 1,
  "matches": [
    {
      "match_id": "R1M1",
      "player_A_id": "P01",
      "player_B_id": "P02",
      "referee_endpoint": "http://localhost:8001/mcp"
    },
    {
      "match_id": "R1M2",
      "player_A_id": "P03",
      "player_B_id": "P04",
      "referee_endpoint": "http://localhost:8001/mcp"
    }
  ]
}
```

**State Changes:**
- League Manager: Round 1 → "ANNOUNCED"
- Players: Aware of upcoming matches

---

### 3.4 Phase 4.1: Game Invitations

**Timeline:** Start of each match

**Actors:** Referee, Player A, Player B

**Flow:**

```
Referee REF01            Player P01              Player P02
     |                        |                        |
     | GAME_INVITATION        |                        |
     |----------------------->|                        |
     |  match_id: R1M1        |                        |
     |  role: PLAYER_A        |                        |
     |  opponent_id: P02      |                        |
     |                        |                        |
     |                   (Accept invitation)           |
     |                        |                        |
     | GAME_JOIN_ACK          |                        |
     |<-----------------------|                        |
     |  accept: true          |                        |
     |                        |                        |
     | GAME_INVITATION        |                        |
     |----------------------------------------------->|
     |  match_id: R1M1        |                        |
     |  role: PLAYER_B        |                        |
     |  opponent_id: P01      |                        |
     |                        |                        |
     |                        |                  (Accept)
     |                        |                        |
     | GAME_JOIN_ACK          |                        |
     |<-----------------------------------------------|
     |  accept: true          |                        |
     |                        |                        |
     | (Both accepted - proceed to choice collection) |
```

**Timeout:** 5 seconds per player

**State Changes:**
- Referee: Game state → "WAITING_FOR_PLAYERS"
- Referee: After both ACKs → "COLLECTING_CHOICES"

**Error Handling:**
- If ANY player timeout/reject → Abort game → Report to League Manager

---

### 3.5 Phase 4.2: Choice Collection (CRITICAL)

**Timeline:** After both players accepted

**Actors:** Referee, Player A, Player B

**CRITICAL REQUIREMENT:** Choices MUST be collected **simultaneously** to prevent timing advantage.

**Flow:**

```
Referee REF01            Player P01              Player P02
     |                        |                        |
     | CHOOSE_PARITY_CALL     |                        |
     |----------------------->|                        |
     |  deadline: T+30s       |                        |
     |                        |                        |
     | CHOOSE_PARITY_CALL     |                        |
     |----------------------------------------------->|
     |  deadline: T+30s       |                        |
     |                        |                        |
     |                   (Strategy computation)  (Strategy computation)
     |                        |                        |
     | CHOOSE_PARITY_RESPONSE |                        |
     |<-----------------------|                        |
     |  choice: "even"        |                        |
     |                        |                        |
     | CHOOSE_PARITY_RESPONSE |                        |
     |<-----------------------------------------------|
     |  choice: "odd"         |                        |
     |                        |                        |
     | (Both choices received - proceed to drawing)   |
```

**Implementation (Simultaneous):**
```python
# CORRECT: Both calls sent at same time
results = await asyncio.gather(
    call_player_A(),
    call_player_B()
)

# WRONG: Sequential (gives timing advantage)
choice_A = await call_player_A()
choice_B = await call_player_B()  # P02 knows P01 already responded
```

**Timeout:** 30 seconds per player

**State Changes:**
- Referee: After both responses → "DRAWING_NUMBER"

**Error Handling:**
- If ANY player timeout → Technical loss for that player
- If invalid choice (not "even" or "odd") → Technical loss

---

### 3.6 Phase 4.3: Number Drawing & Evaluation

**Timeline:** After both choices received

**Actors:** Referee (internal)

**Flow:**

```
Referee (Internal State Machine)
     |
     | Draw number (1-10, cryptographic random)
     | drawn_number = 8
     |
     | Determine parity
     | number_parity = "even"
     |
     | Compare choices
     | P01: "even" → CORRECT ✓
     | P02: "odd"  → WRONG ✗
     |
     | Determine winner
     | winner = P01
     |
     | State: DRAWING_NUMBER → EVALUATING → FINISHED
     |
```

**Implementation:**
```python
import secrets

# 1. Draw number (cryptographically secure)
drawn_number = secrets.randbelow(10) + 1  # 1-10

# 2. Determine parity
number_parity = "even" if drawn_number % 2 == 0 else "odd"

# 3. Find winner
winner = None
for player_id, choice in choices.items():
    if choice == number_parity:
        winner = player_id
        break

# 4. Create result
result = {
    "status": "WIN",
    "winner_player_id": winner,
    "drawn_number": drawn_number,
    "number_parity": number_parity,
    "choices": choices
}
```

**State Changes:**
- Referee: "DRAWING_NUMBER" → "EVALUATING" → "FINISHED"

---

### 3.7 Phase 4.4: Result Notification

**Timeline:** After winner determined

**Actors:** Referee, Player A, Player B

**Flow:**

```
Referee REF01            Player P01              Player P02
     |                        |                        |
     | GAME_OVER              |                        |
     |----------------------->|                        |
     |  winner: P01           |                        |
     |  drawn_number: 8       |                        |
     |  choices: {...}        |                        |
     |                        |                        |
     |                  (Update history)               |
     |                        |                        |
     | GAME_OVER              |                        |
     |----------------------------------------------->|
     |  winner: P01           |                        |
     |  drawn_number: 8       |                        |
     |  choices: {...}        |                        |
     |                        |                        |
     |                        |                  (Update history)
```

**Message Content:**
```json
{
  "message_type": "GAME_OVER",
  "match_id": "R1M1",
  "game_result": {
    "status": "WIN",
    "winner_player_id": "P01",
    "drawn_number": 8,
    "number_parity": "even",
    "choices": {
      "P01": "even",
      "P02": "odd"
    }
  }
}
```

**Player Actions:**
1. Update match history
2. Update opponent profile (for adaptive strategy)
3. Update local statistics
4. Return acknowledgment

**Timeout:** None (fire-and-forget notification)

---

### 3.8 Phase 4.5: Result Reporting

**Timeline:** After notifying players

**Actors:** Referee, League Manager

**Flow:**

```
Referee REF01            League Manager
     |                        |
     | MATCH_RESULT_REPORT    |
     |----------------------->|
     |  winner: P01           |
     |  score: {P01:3, P02:0} |
     |                        |
     |                  (Update standings)
     |                  (Check if round complete)
     |                        |
     | ACK                    |
     |<-----------------------|
     |                        |
```

**Message Content:**
```json
{
  "message_type": "MATCH_RESULT_REPORT",
  "round_id": 1,
  "match_id": "R1M1",
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
}
```

**League Manager Actions:**
1. Update standings (P01 +3 points, P02 +0 points)
2. Mark match R1M1 as complete
3. Check if all round 1 matches complete
4. If yes → Proceed to Phase 5 (Round Completion)

---

### 3.9 Phase 5: Round Completion

**Timeline:** After all matches in round complete

**Actors:** League Manager, All Players

**Flow:**

```
League Manager          Player P01 ... P04
     |                        |
     | (All matches complete) |
     |                        |
     | Calculate standings    |
     |                        |
     | LEAGUE_STANDINGS_UPDATE|
     |----------------------->|
     |  standings: [...]      |
     |                        |
     | ROUND_COMPLETED        |
     |----------------------->|
     |  round_id: 1           |
     |  next_round_id: 2      |
     |                        |
```

**Standings Update:**
```json
{
  "message_type": "LEAGUE_STANDINGS_UPDATE",
  "round_id": 1,
  "standings": [
    {"rank": 1, "player_id": "P01", "points": 3, "wins": 1, "losses": 0},
    {"rank": 2, "player_id": "P03", "points": 1, "wins": 0, "draws": 1},
    {"rank": 3, "player_id": "P04", "points": 1, "wins": 0, "draws": 1},
    {"rank": 4, "player_id": "P02", "points": 0, "wins": 0, "losses": 1}
  ]
}
```

**State Changes:**
- League Manager: Round 1 → "COMPLETED"
- League Manager: Round 2 → "PENDING"
- Players: Update awareness of standings

**Next Action:**
- If more rounds → Loop back to Phase 3 (Round Announcement)
- If no more rounds → Proceed to Phase 6 (League Completion)

---

### 3.10 Phase 6: League Completion

**Timeline:** After all rounds complete

**Actors:** League Manager, All Players

**Flow:**

```
League Manager          Player P01 ... P04
     |                        |
     | LEAGUE_COMPLETED       |
     |----------------------->|
     |  champion: P01         |
     |  final_standings: [...] |
     |                        |
     | Archive results        |
     | Tournament END         |
```

**Message Content:**
```json
{
  "message_type": "LEAGUE_COMPLETED",
  "total_rounds": 3,
  "total_matches": 6,
  "champion": {
    "player_id": "P01",
    "display_name": "Agent Alpha",
    "points": 7
  },
  "final_standings": [...]
}
```

---

## 4. State Transitions

### 4.1 League Manager States

```
STARTUP → ACCEPTING_REGISTRATIONS → SCHEDULING → RUNNING_TOURNAMENT → COMPLETED
```

**Detailed:**
```
STARTUP
  ↓
ACCEPTING_REGISTRATIONS
  ↓ (Admin triggers start)
SCHEDULING (Internal - create schedule)
  ↓
ROUND_1_PENDING
  ↓ (Announce round)
ROUND_1_ANNOUNCED
  ↓ (Matches dispatched)
ROUND_1_IN_PROGRESS
  ↓ (All matches complete)
ROUND_1_COMPLETED
  ↓
ROUND_2_PENDING
  ... (repeat for each round) ...
  ↓
TOURNAMENT_COMPLETED
```

### 4.2 Referee (Game) States

```
IDLE → WAITING_FOR_PLAYERS → COLLECTING_CHOICES → DRAWING_NUMBER → EVALUATING → FINISHED

Any state → ABORTED (on timeout/error)
```

**Valid Transitions:**
```python
TRANSITIONS = {
    "IDLE": {"WAITING_FOR_PLAYERS"},
    "WAITING_FOR_PLAYERS": {"COLLECTING_CHOICES", "ABORTED"},
    "COLLECTING_CHOICES": {"DRAWING_NUMBER", "ABORTED"},
    "DRAWING_NUMBER": {"EVALUATING"},
    "EVALUATING": {"FINISHED"},
    "FINISHED": set(),
    "ABORTED": set()
}
```

### 4.3 Player States

```
UNREGISTERED → REGISTERED → WAITING_FOR_ROUND → IN_GAME → WAITING_FOR_ROUND
                                                      ↑              ↓
                                                      └──────────────┘
                                                      (Loop for each match)
```

---

## 5. Message Sequence Diagrams

### 5.1 Complete Match Flow

```
League Mgr    Referee       Player A      Player B
    |            |              |             |
    | (Round announcement)      |             |
    |--------------------------->             |
    |                           |             |
    | Assign match              |             |
    |----------->|              |             |
    |            |              |             |
    |            | GAME_INVITATION            |
    |            |------------->|             |
    |            |              |             |
    |            | GAME_JOIN_ACK|             |
    |            |<-------------|             |
    |            |              |             |
    |            | GAME_INVITATION            |
    |            |-------------------------->|
    |            |              |             |
    |            | GAME_JOIN_ACK              |
    |            |<--------------------------|
    |            |              |             |
    |            | CHOOSE_PARITY_CALL         |
    |            |------------->|             |
    |            | CHOOSE_PARITY_CALL         |
    |            |-------------------------->|
    |            |              |             |
    |            | CHOOSE_PARITY_RESPONSE     |
    |            |<-------------|             |
    |            | CHOOSE_PARITY_RESPONSE     |
    |            |<--------------------------|
    |            |              |             |
    |            | (Draw number, evaluate)    |
    |            |              |             |
    |            | GAME_OVER    |             |
    |            |------------->|             |
    |            | GAME_OVER    |             |
    |            |-------------------------->|
    |            |              |             |
    |            | MATCH_RESULT_REPORT        |
    |            |<-----------|              |
    |<-----------|              |             |
    |            |              |             |
    | (Update standings)        |             |
```

---

## 6. Timeout Handling

### 6.1 Timeout Values

| Operation | Timeout | Consequence |
|-----------|---------|-------------|
| GAME_INVITATION → GAME_JOIN_ACK | 5 seconds | Match aborted, technical loss |
| CHOOSE_PARITY_CALL → CHOOSE_PARITY_RESPONSE | 30 seconds | Technical loss for timeout player |
| MATCH_RESULT_REPORT → ACK | 10 seconds | Retry 3 times, then log error |

### 6.2 Retry Logic

**For transient errors:**
```python
config = RetryConfig(
    max_retries=3,
    initial_delay=2.0,
    backoff_multiplier=2.0
)

# Retry sequence:
# Attempt 1: Immediate
# Attempt 2: After 2s delay
# Attempt 3: After 4s delay
# Attempt 4: After 8s delay
```

---

## 7. Error Scenarios

### 7.1 Player No-Show

**Scenario:** Player doesn't respond to GAME_INVITATION within 5 seconds

**Flow:**
1. Referee: Timeout on GAME_INVITATION
2. Referee: Retry up to 3 times
3. Referee: After 3 failures → Abort game
4. Referee: Report to League Manager with error
5. League Manager: Award technical loss (0 points) to no-show player
6. League Manager: Award technical win (3 points) to other player

### 7.2 Player Timeout During Choice

**Scenario:** Player doesn't respond to CHOOSE_PARITY_CALL within 30 seconds

**Flow:**
1. Referee: Timeout on CHOOSE_PARITY_CALL
2. Referee: Other player's choice is valid
3. Referee: Award technical loss to timeout player (0 points)
4. Referee: Award technical win to other player (3 points)
5. Referee: Report to League Manager

### 7.3 Invalid Choice

**Scenario:** Player returns choice other than "even" or "odd"

**Flow:**
1. Referee: Validate choice
2. Referee: Invalid choice detected (e.g., "maybe")
3. Referee: Award technical loss to invalid player (0 points)
4. Referee: Award technical win to other player (3 points)
5. Referee: Report to League Manager

### 7.4 Referee Crash

**Scenario:** Referee crashes mid-game

**Flow:**
1. Players: Timeout waiting for response
2. Players: Log error
3. League Manager: Detects referee unresponsive (heartbeat/health check)
4. League Manager: Reassigns match to different referee
5. New Referee: Restarts match from beginning

---

## 8. Success Criteria

### 8.1 Functional Success

- ✅ All messages follow protocol exactly
- ✅ All state transitions are valid
- ✅ Timeouts enforced correctly
- ✅ Errors handled gracefully
- ✅ Results calculated correctly

### 8.2 Performance Success

- ✅ Invitation response < 5 seconds
- ✅ Choice response < 30 seconds
- ✅ Match completion < 2 minutes (typical)
- ✅ Round completion < 10 minutes (for 4 players, 2 matches/round)

### 8.3 Reliability Success

- ✅ 100% of matches complete or properly aborted
- ✅ 0% data corruption (atomic writes)
- ✅ 100% of results reported to League Manager
- ✅ < 5% timeout rate under normal conditions

---

## Summary

The Game Flow Logic provides:

✅ **Complete Message Sequences** for all phases
✅ **State Transition Rules** with validation
✅ **Timeout Enforcement** with retry logic
✅ **Error Scenarios** with recovery paths
✅ **Simultaneous Move Collection** for fairness
✅ **Performance Criteria** for success

**Key Principles:**
1. **Fairness:** Simultaneous move collection
2. **Reliability:** Retry logic and error recovery
3. **Auditability:** Complete message logging
4. **Determinism:** Cryptographic random for fairness

---

**Related Documents:**
- [referee-architecture.md](./referee-architecture.md) - Referee implementation
- [player-agent-architecture.md](./player-agent-architecture.md) - Player implementation
- [league-manager-architecture.md](./league-manager-architecture.md) - League Manager implementation

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
