# Product Requirements Document (PRD)
# Game Protocol Messages - Complete Message Catalog

**Document Version:** 1.0
**Date:** 2025-12-20
**Status:** Draft
**Product Owner:** AI Development Course Team
**Target Release:** Phase 1 - Foundation
**Related Documents:**
- `league-system-prd.md` (League Management System)
- `even-odd-game-prd.md` (Even/Odd Game Rules)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Message Architecture](#message-architecture)
3. [Registration Messages](#registration-messages)
4. [Round Management Messages](#round-management-messages)
5. [Game Flow Messages](#game-flow-messages)
6. [Even/Odd Specific Messages](#evenodd-specific-messages)
7. [Result & Standings Messages](#result--standings-messages)
8. [Query Messages](#query-messages)
9. [Error Messages](#error-messages)
10. [Message Summary & Validation Rules](#message-summary--validation-rules)
11. [User Stories](#user-stories)
12. [Acceptance Criteria](#acceptance-criteria)
13. [Success Metrics](#success-metrics)
14. [Technical Constraints](#technical-constraints)

---

## 1. Executive Summary

### 1.1 Purpose
This document defines all 18 message types in the League Protocol v2.1. Each message structure is specified exactly to ensure all student agents can communicate successfully regardless of implementation language.

### 1.2 Critical Importance
**MANDATORY:** All students must implement these message structures exactly as specified. Even minor deviations (e.g., different field names, wrong data types) will cause communication failures.

### 1.3 Message Categories
- **Registration:** 4 messages (referee + player registration)
- **Round Management:** 3 messages (announcement, completion, league completion)
- **Game Flow:** 3 messages (invitation, join acknowledgment, game over)
- **Game Specific:** 2 messages (choose parity call/response)
- **Results:** 2 messages (result report, standings update)
- **Queries:** 2 messages (query request/response)
- **Errors:** 2 messages (league error, game error)

**Total:** 18 message types

---

## 2. Message Architecture

### 2.1 Message Envelope (Inherited from League Protocol)

**Reminder:** All messages must include the standard envelope fields defined in `league-system-prd.md`:

```json
{
  "protocol": "league.v2",
  "message_type": "SPECIFIC_MESSAGE_TYPE",
  "sender": "type:id",
  "timestamp": "YYYY-MM-DDTHH:MM:SSZ",
  "conversation_id": "unique_conversation_id"
}
```

**Note:** The envelope is NOT repeated in each message example below (to reduce verbosity), but it is MANDATORY in actual implementation.

### 2.2 Message Direction Notation

**Format:** `Sender → Receiver`

Examples:
- `Referee → Player`: Referee sends to Player
- `Player → Referee`: Player sends to Referee
- `League → All Players`: League Manager broadcasts to all registered players

---

## 3. Registration Messages

### 3.1 REFEREE_REGISTER_REQUEST

**Direction:** Referee → League Manager
**Purpose:** Referee registers with league before officiating games
**Expected Response:** REFEREE_REGISTER_RESPONSE
**Timeout:** 10 seconds

#### 3.1.1 Message Structure

```json
{
  "message_type": "REFEREE_REGISTER_REQUEST",
  "referee_meta": {
    "display_name": "Referee Alpha",
    "version": "1.0.0",
    "game_types": ["even_odd"],
    "contact_endpoint": "http://localhost:8001/mcp",
    "max_concurrent_matches": 2
  }
}
```

#### 3.1.2 Field Specifications

**referee_meta** (object, required):
- **display_name** (string, required): Human-readable referee name
  - Min length: 1 character
  - Max length: 50 characters
  - Example: "Referee Alpha", "REF-01"

- **version** (string, required): Referee software version
  - Format: Semantic versioning (MAJOR.MINOR.PATCH)
  - Example: "1.0.0", "2.1.3"

- **game_types** (array of strings, required): List of supported game types
  - Minimum 1 game type
  - Valid values: "even_odd", "tic_tac_toe" (future)
  - Example: ["even_odd"]

- **contact_endpoint** (string, required): Referee's HTTP endpoint for receiving messages
  - Format: Valid HTTP/HTTPS URL
  - Must be reachable from League Manager
  - Example: "http://localhost:8001/mcp", "https://referee01.example.com/mcp"

- **max_concurrent_matches** (integer, required): Maximum games referee can handle simultaneously
  - Minimum: 1
  - Maximum: 10
  - Recommended: 2-5
  - Example: 2

#### 3.1.3 User Story

> **As a** referee agent
> **I want to** register with the League Manager
> **So that** I can be assigned matches to officiate during the tournament

#### 3.1.4 Acceptance Criteria

- ✅ Referee sends registration request before league starts
- ✅ All required fields present and valid
- ✅ game_types includes at least "even_odd"
- ✅ contact_endpoint is reachable (League Manager validates)
- ✅ Response received within 10 seconds

---

### 3.2 REFEREE_REGISTER_RESPONSE

**Direction:** League Manager → Referee
**Purpose:** Confirm referee registration or reject with reason
**Triggered By:** REFEREE_REGISTER_REQUEST
**Timeout:** N/A (response message)

#### 3.2.1 Message Structure

**Success Response:**
```json
{
  "message_type": "REFEREE_REGISTER_RESPONSE",
  "status": "ACCEPTED",
  "referee_id": "REF01",
  "reason": null
}
```

**Rejection Response:**
```json
{
  "message_type": "REFEREE_REGISTER_RESPONSE",
  "status": "REJECTED",
  "referee_id": null,
  "reason": "League already started"
}
```

#### 3.2.2 Field Specifications

- **status** (string, required): Registration outcome
  - Allowed values: "ACCEPTED" or "REJECTED"
  - Case-sensitive

- **referee_id** (string, nullable): Assigned referee identifier
  - Format: "REF" + two-digit number (REF01, REF02, ...)
  - Only present if status = "ACCEPTED"
  - Null if status = "REJECTED"

- **reason** (string, nullable): Rejection reason
  - Only present if status = "REJECTED"
  - Human-readable explanation
  - Examples: "League already started", "Unsupported game type", "Endpoint unreachable"
  - Null if status = "ACCEPTED"

#### 3.2.3 Acceptance Criteria

- ✅ Status is exactly "ACCEPTED" or "REJECTED"
- ✅ If ACCEPTED: referee_id assigned, reason is null
- ✅ If REJECTED: referee_id is null, reason provided
- ✅ Referee stores referee_id and auth_token for future messages

---

### 3.3 LEAGUE_REGISTER_REQUEST

**Direction:** Player → League Manager
**Purpose:** Player registers to participate in tournament
**Expected Response:** LEAGUE_REGISTER_RESPONSE
**Timeout:** 10 seconds

#### 3.3.1 Message Structure

```json
{
  "message_type": "LEAGUE_REGISTER_REQUEST",
  "player_meta": {
    "display_name": "Agent Alpha",
    "version": "1.0.0",
    "game_types": ["even_odd"],
    "contact_endpoint": "http://localhost:8101/mcp"
  }
}
```

#### 3.3.2 Field Specifications

**player_meta** (object, required):
- **display_name** (string, required): Human-readable player name
  - Min length: 1 character
  - Max length: 50 characters
  - Example: "Agent Alpha", "StudentBot-123"

- **version** (string, required): Player agent version
  - Format: Semantic versioning
  - Example: "1.0.0"

- **game_types** (array of strings, required): List of supported game types
  - Must include "even_odd" for this tournament
  - Example: ["even_odd"]

- **contact_endpoint** (string, required): Player's HTTP endpoint
  - Format: Valid HTTP/HTTPS URL
  - Must be reachable from referees
  - Example: "http://localhost:8101/mcp"

#### 3.3.3 User Story

> **As a** student developer
> **I want to** register my agent with the league
> **So that** it can participate in the tournament and compete against other agents

#### 3.3.4 Acceptance Criteria

- ✅ Player sends registration before league starts
- ✅ All required fields present and valid
- ✅ contact_endpoint is reachable
- ✅ Unique display_name (recommended, not enforced)
- ✅ Response received within 10 seconds

---

### 3.4 LEAGUE_REGISTER_RESPONSE

**Direction:** League Manager → Player
**Purpose:** Confirm player registration or reject with reason
**Triggered By:** LEAGUE_REGISTER_REQUEST
**Timeout:** N/A (response message)

#### 3.4.1 Message Structure

**Success Response:**
```json
{
  "message_type": "LEAGUE_REGISTER_RESPONSE",
  "status": "ACCEPTED",
  "player_id": "P01",
  "reason": null
}
```

**Rejection Response:**
```json
{
  "message_type": "LEAGUE_REGISTER_RESPONSE",
  "status": "REJECTED",
  "player_id": null,
  "reason": "Registration closed - league already started"
}
```

#### 3.4.2 Field Specifications

- **status** (string, required): "ACCEPTED" or "REJECTED"
- **player_id** (string, nullable): Assigned player identifier
  - Format: "P" + two-digit number (P01, P02, ..., P99)
  - Only present if ACCEPTED
- **reason** (string, nullable): Rejection reason if REJECTED

#### 3.4.3 Common Rejection Reasons

- "Registration closed - league already started"
- "Unsupported game type"
- "Contact endpoint unreachable"
- "Protocol version mismatch"
- "Maximum players reached"

#### 3.4.4 Acceptance Criteria

- ✅ Player receives response within 10 seconds
- ✅ If ACCEPTED: player_id stored for all future messages
- ✅ If REJECTED: reason clearly explains why
- ✅ Player stores auth_token (included in envelope, not shown here)

---

## 4. Round Management Messages

### 4.1 ROUND_ANNOUNCEMENT

**Direction:** League Manager → All Players
**Purpose:** Announce round start with complete match schedule
**Expected Response:** None (broadcast message)
**Timing:** Sent before each round begins (at least 60 seconds before first match)

#### 4.1.1 Message Structure

```json
{
  "message_type": "ROUND_ANNOUNCEMENT",
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
}
```

#### 4.1.2 Field Specifications

- **league_id** (string, required): League identifier
  - Example: "league_2025_even_odd"

- **round_id** (integer, required): Round number (1-indexed)
  - Minimum: 1
  - Increments sequentially
  - Example: 1, 2, 3

- **matches** (array of objects, required): List of all matches in this round
  - Minimum: 1 match
  - Maximum: N/2 matches (where N = number of players)

**Match Object:**
- **match_id** (string, required): Unique match identifier
  - Format: "R{round_id}M{match_number}"
  - Example: "R1M1", "R2M3"

- **game_type** (string, required): Type of game
  - Value: "even_odd" (for this tournament)

- **player_A_id** (string, required): First player ID
  - Example: "P01"

- **player_B_id** (string, required): Second player ID
  - Example: "P02"

- **referee_endpoint** (string, required): Referee's HTTP endpoint for this match
  - Players don't contact referee directly (referee contacts them)
  - Included for transparency/logging
  - Example: "http://localhost:8001/mcp"

#### 4.1.3 User Story

> **As a** player agent
> **I want to** know which opponents I'll face in the upcoming round
> **So that** I can prepare strategy and anticipate invitations

#### 4.1.4 Acceptance Criteria

- ✅ Broadcast to all registered players
- ✅ Sent at least 60 seconds before first match starts
- ✅ Includes all matches for the round
- ✅ No duplicate player assignments (each player plays at most once per round)
- ✅ No player plays themselves

---

### 4.2 ROUND_COMPLETED

**Direction:** League Manager → All Players & Referees
**Purpose:** Notify that a round has finished and provide summary
**Expected Response:** None (broadcast message)
**Timing:** Sent immediately after last match of round completes

#### 4.2.1 Message Structure

```json
{
  "message_type": "ROUND_COMPLETED",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "matches_completed": 2,
  "next_round_id": 2,
  "summary": {
    "total_matches": 2,
    "wins": 1,
    "draws": 1,
    "technical_losses": 0
  }
}
```

#### 4.2.2 Field Specifications

- **league_id** (string, required): League identifier
- **round_id** (integer, required): Round that just completed
- **matches_completed** (integer, required): Number of matches that finished
- **next_round_id** (integer, nullable): Next round number
  - Null if this was the final round
  - Example: 2, 3, null

**summary** (object, required): Round statistics
- **total_matches** (integer): Matches scheduled for round
- **wins** (integer): Number of matches with clear winner (not draws)
- **draws** (integer): Number of tie games
- **technical_losses** (integer): Matches decided by timeout/error

#### 4.2.3 Acceptance Criteria

- ✅ Sent only after ALL matches in round complete
- ✅ summary.wins + summary.draws + summary.technical_losses = total_matches
- ✅ next_round_id is null for final round
- ✅ Broadcast to all players and referees

---

### 4.3 LEAGUE_COMPLETED

**Direction:** League Manager → All Agents (Players & Referees)
**Purpose:** Announce tournament end and final standings
**Expected Response:** None (final broadcast message)
**Timing:** Sent after all rounds complete

#### 4.3.1 Message Structure

```json
{
  "message_type": "LEAGUE_COMPLETED",
  "league_id": "league_2025_even_odd",
  "total_rounds": 3,
  "total_matches": 6,
  "champion": {
    "player_id": "P01",
    "display_name": "Agent Alpha",
    "points": 9
  },
  "final_standings": [
    {"rank": 1, "player_id": "P01", "display_name": "Agent Alpha", "points": 9},
    {"rank": 2, "player_id": "P03", "display_name": "Agent Gamma", "points": 5},
    {"rank": 3, "player_id": "P02", "display_name": "Agent Beta", "points": 3},
    {"rank": 4, "player_id": "P04", "display_name": "Agent Delta", "points": 1}
  ]
}
```

#### 4.3.2 Field Specifications

- **league_id** (string, required): League identifier
- **total_rounds** (integer, required): Number of rounds played
- **total_matches** (integer, required): Total matches across all rounds

**champion** (object, required): Tournament winner
- **player_id** (string): Winner's player ID
- **display_name** (string): Winner's name
- **points** (integer): Total points earned

**final_standings** (array of objects, required): Complete ranking
- Sorted by rank (ascending)
- All registered players included

**Standing Object:**
- **rank** (integer): Final rank (1 = champion)
- **player_id** (string): Player identifier
- **display_name** (string): Player name
- **points** (integer): Total points

#### 4.3.3 User Story

> **As a** student developer
> **I want to** see the final tournament results and my ranking
> **So that** I know how well my agent performed

#### 4.3.4 Acceptance Criteria

- ✅ Sent only after all rounds complete
- ✅ champion is player with highest points
- ✅ final_standings sorted by rank
- ✅ All registered players included in standings
- ✅ Broadcast to all agents

---

## 5. Game Flow Messages

### 5.1 GAME_INVITATION

**Direction:** Referee → Player
**Purpose:** Invite player to a match
**Expected Response:** GAME_JOIN_ACK
**Timeout:** 5 seconds

#### 5.1.1 Message Structure

```json
{
  "message_type": "GAME_INVITATION",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "match_id": "R1M1",
  "game_type": "even_odd",
  "role_in_match": "PLAYER_A",
  "opponent_id": "P02",
  "conversation_id": "convr1m1001"
}
```

#### 5.1.2 Field Specifications

- **league_id** (string, required): League identifier
- **round_id** (integer, required): Round number
- **match_id** (string, required): Match identifier
- **game_type** (string, required): "even_odd"

- **role_in_match** (string, required): Player's role
  - Allowed values: "PLAYER_A" or "PLAYER_B"
  - No gameplay difference, only for logging/tracking

- **opponent_id** (string, required): Opponent's player ID
  - Example: "P02"
  - Allows player to look up opponent's history

- **conversation_id** (string, required): Unique conversation ID for this match
  - Used to correlate all messages in this game
  - Example: "convr1m1001"

#### 5.1.3 User Story

> **As a** player agent
> **I want to** receive match invitations with opponent information
> **So that** I can confirm readiness and prepare strategy

#### 5.1.4 Acceptance Criteria

- ✅ Sent to both players (Player A and Player B)
- ✅ Includes opponent_id for strategy preparation
- ✅ conversation_id unique per match
- ✅ Player must respond within 5 seconds

---

### 5.2 GAME_JOIN_ACK

**Direction:** Player → Referee
**Purpose:** Confirm arrival and readiness for match
**Triggered By:** GAME_INVITATION
**Timeout:** 5 seconds (included in GAME_INVITATION timeout)

#### 5.2.1 Message Structure

**Accept Invitation:**
```json
{
  "message_type": "GAME_JOIN_ACK",
  "match_id": "R1M1",
  "player_id": "P01",
  "arrival_timestamp": "20250115T10:30:00Z",
  "accept": true
}
```

**Reject Invitation:**
```json
{
  "message_type": "GAME_JOIN_ACK",
  "match_id": "R1M1",
  "player_id": "P01",
  "arrival_timestamp": "20250115T10:30:00Z",
  "accept": false
}
```

#### 5.2.2 Field Specifications

- **match_id** (string, required): Match identifier (must match invitation)
- **player_id** (string, required): Player's ID
- **arrival_timestamp** (string, required): Player's local timestamp (ISO 8601 UTC)
  - Used for debugging latency issues
  - Must be in UTC timezone

- **accept** (boolean, required): Whether player accepts invitation
  - `true`: Ready to play
  - `false`: Reject invitation (results in TECHNICAL_LOSS)

#### 5.2.3 Acceptance Criteria

- ✅ Sent within 5 seconds of receiving GAME_INVITATION
- ✅ match_id matches invitation
- ✅ arrival_timestamp in UTC format
- ✅ If accept=false → player forfeits match (0 points)
- ✅ If timeout (no response) → player forfeits match (0 points)

---

### 5.3 GAME_OVER

**Direction:** Referee → Both Players
**Purpose:** Notify players of match outcome
**Expected Response:** None (informational message)
**Timeout:** 5 seconds (for acknowledgment, optional)

#### 5.3.1 Message Structure

**Standard Win:**
```json
{
  "message_type": "GAME_OVER",
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

**Draw:**
```json
{
  "message_type": "GAME_OVER",
  "match_id": "R1M1",
  "game_type": "even_odd",
  "game_result": {
    "status": "DRAW",
    "winner_player_id": null,
    "drawn_number": 4,
    "number_parity": "even",
    "choices": {
      "P01": "odd",
      "P02": "odd"
    },
    "reason": "Both chose odd, number was 4 (even) - both incorrect"
  }
}
```

**Technical Loss:**
```json
{
  "message_type": "GAME_OVER",
  "match_id": "R1M1",
  "game_type": "even_odd",
  "game_result": {
    "status": "TECHNICAL_LOSS",
    "winner_player_id": "P01",
    "drawn_number": null,
    "number_parity": null,
    "choices": {
      "P01": "even",
      "P02": null
    },
    "reason": "P02 failed to respond within timeout - P01 wins by default"
  }
}
```

#### 5.3.2 Field Specifications

- **match_id** (string, required): Match identifier
- **game_type** (string, required): "even_odd"

**game_result** (object, required):
- **status** (string, required): Match outcome type
  - Allowed values: "WIN", "DRAW", "TECHNICAL_LOSS"

- **winner_player_id** (string, nullable): Winner's player ID
  - Null if draw
  - Player ID if win or technical_loss

- **drawn_number** (integer, nullable): Random number drawn (1-10)
  - Null if technical_loss (game didn't reach draw phase)
  - Integer 1-10 if game completed normally

- **number_parity** (string, nullable): Parity of drawn number
  - Allowed values: "even", "odd", null
  - Null if technical_loss

- **choices** (object, required): Map of player_id → choice
  - Keys: player IDs participating in match
  - Values: "even", "odd", or null (if player didn't respond)
  - Example: {"P01": "even", "P02": "odd"}

- **reason** (string, required): Human-readable explanation
  - Examples:
    - "P01 chose even, number was 8 (even)"
    - "Both chose odd, number was 4 (even) - both incorrect"
    - "P02 failed to respond within timeout - P01 wins by default"

#### 5.3.3 User Story

> **As a** player agent
> **I want to** receive complete match results including opponent's choice
> **So that** I can learn from the game and update my strategy

#### 5.3.4 Acceptance Criteria

- ✅ Sent to both players (identical message)
- ✅ Includes all relevant data: choices, number, winner
- ✅ Transparent reveal of opponent's choice
- ✅ Clear reason explaining outcome
- ✅ status field correctly reflects outcome type

---

## 6. Even/Odd Specific Messages

### 6.1 CHOOSE_PARITY_CALL

**Direction:** Referee → Player
**Purpose:** Request player's choice (even or odd)
**Expected Response:** CHOOSE_PARITY_RESPONSE
**Timeout:** 30 seconds

#### 6.1.1 Message Structure

```json
{
  "message_type": "CHOOSE_PARITY_CALL",
  "match_id": "R1M1",
  "player_id": "P01",
  "game_type": "even_odd",
  "context": {
    "opponent_id": "P02",
    "round_id": 1,
    "your_standings": {
      "wins": 2,
      "losses": 1,
      "draws": 0
    }
  },
  "deadline": "20250115T10:30:30Z"
}
```

#### 6.1.2 Field Specifications

- **match_id** (string, required): Match identifier
- **player_id** (string, required): Player being asked to choose
- **game_type** (string, required): "even_odd"

**context** (object, optional but recommended): Strategic context
- **opponent_id** (string): Who player is playing against
- **round_id** (integer): Current round number
- **your_standings** (object, optional): Player's current record
  - **wins** (integer): Total wins so far
  - **losses** (integer): Total losses so far
  - **draws** (integer): Total draws so far

- **deadline** (string, required): UTC timestamp when response must be received
  - ISO 8601 format with 'Z' suffix
  - Example: "20250115T10:30:30Z"
  - Calculated as: current_time + 30 seconds

#### 6.1.3 User Story

> **As a** player agent
> **I want to** receive strategic context with choice requests
> **So that** I can make informed decisions based on tournament standings

#### 6.1.4 Acceptance Criteria

- ✅ Sent after both players confirmed arrival
- ✅ Sent simultaneously to both players (not sequentially)
- ✅ Includes deadline for timeout enforcement
- ✅ context provides useful strategic information
- ✅ Player must respond within 30 seconds

---

### 6.2 CHOOSE_PARITY_RESPONSE

**Direction:** Player → Referee
**Purpose:** Provide choice (even or odd)
**Triggered By:** CHOOSE_PARITY_CALL
**Timeout:** 30 seconds (enforced by referee)

#### 6.2.1 Message Structure

```json
{
  "message_type": "CHOOSE_PARITY_RESPONSE",
  "match_id": "R1M1",
  "player_id": "P01",
  "parity_choice": "even"
}
```

#### 6.2.2 Field Specifications

- **match_id** (string, required): Match identifier (must match request)
- **player_id** (string, required): Player making choice
- **parity_choice** (string, required): Player's choice
  - **CRITICAL:** Must be exactly "even" or "odd" (lowercase, string type)
  - ❌ Invalid: "Even", "EVEN", "e", 0, true, null, ""

#### 6.2.3 Validation Rules

**Valid Choices:**
- ✅ `"even"` (lowercase string)
- ✅ `"odd"` (lowercase string)

**Invalid Choices (result in E004 error):**
- ❌ `"Even"` (wrong case)
- ❌ `"EVEN"` (wrong case)
- ❌ `"e"` (abbreviation not allowed)
- ❌ `"maybe"` (not a valid choice)
- ❌ `0` (must be string, not integer)
- ❌ `false` (must be string, not boolean)
- ❌ `null` (must be present)
- ❌ `""` (empty string not allowed)

#### 6.2.4 Error Handling

**If invalid choice:**
1. Referee sends GAME_ERROR with error_code E004 (INVALID_PARITY_CHOICE)
2. Player can retry within remaining timeout window
3. If timeout expires before valid choice → TECHNICAL_LOSS

**Example Error Response:**
```json
{
  "message_type": "GAME_ERROR",
  "error_code": "E004",
  "error_name": "INVALID_PARITY_CHOICE",
  "error_description": "Choice must be 'even' or 'odd', got 'Even'",
  "retryable": true,
  "time_remaining": 15.3
}
```

#### 6.2.5 Acceptance Criteria

- ✅ Sent within 30 seconds of receiving CHOOSE_PARITY_CALL
- ✅ parity_choice is exactly "even" or "odd" (case-sensitive)
- ✅ parity_choice is string type (not int or bool)
- ✅ match_id matches request
- ✅ If invalid → error sent with retry opportunity
- ✅ If timeout → TECHNICAL_LOSS assigned

---

## 7. Result & Standings Messages

### 7.1 MATCH_RESULT_REPORT

**Direction:** Referee → League Manager
**Purpose:** Report match outcome for standings update
**Expected Response:** None (League Manager acknowledges via LEAGUE_STANDINGS_UPDATE)
**Timeout:** 10 seconds

#### 7.1.1 Message Structure

```json
{
  "message_type": "MATCH_RESULT_REPORT",
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
}
```

#### 7.1.2 Field Specifications

- **league_id** (string, required): League identifier
- **round_id** (integer, required): Round number
- **match_id** (string, required): Match identifier
- **game_type** (string, required): "even_odd"

**result** (object, required):
- **winner** (string, nullable): Winner's player_id
  - Null if draw
  - Player ID if win or technical_loss

- **score** (object, required): Points awarded
  - Keys: player IDs
  - Values: points (3, 1, or 0)
  - Example: {"P01": 3, "P02": 0} (win/loss)
  - Example: {"P01": 1, "P02": 1} (draw)

- **details** (object, required): Game-specific details
  - **drawn_number** (integer, nullable): Random number (1-10)
  - **choices** (object, required): Map of player_id → choice
    - Values: "even", "odd", or null

#### 7.1.3 Acceptance Criteria

- ✅ Sent immediately after match concludes
- ✅ score correctly reflects win (3-0), draw (1-1), or technical_loss
- ✅ details include all relevant game data
- ✅ League Manager updates standings within 5 seconds

---

### 7.2 LEAGUE_STANDINGS_UPDATE

**Direction:** League Manager → All Players
**Purpose:** Broadcast updated tournament standings
**Expected Response:** None (broadcast message)
**Timing:** Sent after each match result received

#### 7.2.1 Message Structure

```json
{
  "message_type": "LEAGUE_STANDINGS_UPDATE",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "standings": [
    {
      "rank": 1,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "played": 2,
      "wins": 2,
      "draws": 0,
      "losses": 0,
      "points": 6
    },
    {
      "rank": 2,
      "player_id": "P03",
      "display_name": "Agent Gamma",
      "played": 2,
      "wins": 1,
      "draws": 1,
      "losses": 0,
      "points": 4
    }
  ]
}
```

#### 7.2.2 Field Specifications

- **league_id** (string, required): League identifier
- **round_id** (integer, required): Current round number

**standings** (array of objects, required): Ranked list of all players
- Sorted by rank (ascending: 1, 2, 3, ...)
- All registered players included (even if 0 points)

**Standing Object:**
- **rank** (integer, required): Current rank (1 = first place)
- **player_id** (string, required): Player identifier
- **display_name** (string, required): Player's name
- **played** (integer, required): Games played so far
- **wins** (integer, required): Number of wins
- **draws** (integer, required): Number of draws
- **losses** (integer, required): Number of losses
- **points** (integer, required): Total points
  - Formula: (wins × 3) + (draws × 1) + (losses × 0)

#### 7.2.3 User Story

> **As a** player agent
> **I want to** see updated standings after each match
> **So that** I can track my progress and adjust strategy if needed

#### 7.2.4 Acceptance Criteria

- ✅ Broadcast to all players after each match
- ✅ standings sorted by rank (ascending)
- ✅ Points calculated correctly
- ✅ played = wins + draws + losses
- ✅ Tiebreaker rules applied (see even-odd-game-prd.md)
- ✅ Update latency < 5 seconds after match result

---

## 8. Query Messages

### 8.1 LEAGUE_QUERY

**Direction:** Player or Referee → League Manager
**Purpose:** Request information from league (standings, schedule, stats)
**Expected Response:** LEAGUE_QUERY_RESPONSE
**Timeout:** 10 seconds

#### 8.1.1 Message Structure

**Get Next Match:**
```json
{
  "message_type": "LEAGUE_QUERY",
  "league_id": "league_2025_even_odd",
  "query_type": "GET_NEXT_MATCH",
  "query_params": {
    "player_id": "P01"
  }
}
```

**Get Standings:**
```json
{
  "message_type": "LEAGUE_QUERY",
  "league_id": "league_2025_even_odd",
  "query_type": "GET_STANDINGS",
  "query_params": {}
}
```

**Get Schedule:**
```json
{
  "message_type": "LEAGUE_QUERY",
  "league_id": "league_2025_even_odd",
  "query_type": "GET_SCHEDULE",
  "query_params": {
    "round_id": 2
  }
}
```

**Get Player Stats:**
```json
{
  "message_type": "LEAGUE_QUERY",
  "league_id": "league_2025_even_odd",
  "query_type": "GET_PLAYER_STATS",
  "query_params": {
    "player_id": "P01"
  }
}
```

#### 8.1.2 Field Specifications

- **league_id** (string, required): League identifier
- **query_type** (string, required): Type of information requested
  - Allowed values:
    - "GET_STANDINGS" - Current rankings
    - "GET_SCHEDULE" - Match schedule (full or specific round)
    - "GET_NEXT_MATCH" - Next match for specific player
    - "GET_PLAYER_STATS" - Detailed stats for specific player

- **query_params** (object, required): Query-specific parameters
  - Contents vary by query_type
  - Can be empty object `{}` if no params needed

#### 8.1.3 Acceptance Criteria

- ✅ auth_token included (in envelope)
- ✅ query_type is one of the supported types
- ✅ query_params include required fields for query_type
- ✅ Response received within 10 seconds

---

### 8.2 LEAGUE_QUERY_RESPONSE

**Direction:** League Manager → Original Sender (Player or Referee)
**Purpose:** Provide requested information
**Triggered By:** LEAGUE_QUERY
**Timeout:** N/A (response message)

#### 8.2.1 Message Structure

**Next Match Response:**
```json
{
  "message_type": "LEAGUE_QUERY_RESPONSE",
  "query_type": "GET_NEXT_MATCH",
  "success": true,
  "data": {
    "next_match": {
      "match_id": "R2M1",
      "round_id": 2,
      "opponent_id": "P03",
      "referee_endpoint": "http://localhost:8001/mcp"
    }
  }
}
```

**Standings Response:**
```json
{
  "message_type": "LEAGUE_QUERY_RESPONSE",
  "query_type": "GET_STANDINGS",
  "success": true,
  "data": {
    "standings": [
      {"rank": 1, "player_id": "P01", "points": 9},
      {"rank": 2, "player_id": "P03", "points": 5}
    ]
  }
}
```

**Error Response:**
```json
{
  "message_type": "LEAGUE_QUERY_RESPONSE",
  "query_type": "GET_NEXT_MATCH",
  "success": false,
  "error": {
    "error_code": "E005",
    "error_name": "PLAYER_NOT_REGISTERED",
    "error_description": "Player ID P99 not found in registry"
  }
}
```

#### 8.2.2 Field Specifications

- **query_type** (string, required): Echoes original query type
- **success** (boolean, required): Whether query succeeded

**If success = true:**
- **data** (object, required): Query results
  - Structure varies by query_type

**If success = false:**
- **error** (object, required): Error details
  - **error_code** (string): Error code (e.g., "E005")
  - **error_name** (string): Error name (e.g., "PLAYER_NOT_REGISTERED")
  - **error_description** (string): Human-readable explanation

#### 8.2.3 Acceptance Criteria

- ✅ query_type matches original request
- ✅ If success=true: data contains requested information
- ✅ If success=false: error provides clear explanation
- ✅ Response received within 10 seconds

---

## 9. Error Messages

### 9.1 LEAGUE_ERROR

**Direction:** League Manager → Agent (Player or Referee)
**Purpose:** Notify agent of league-level error
**Expected Response:** None (error notification)

#### 9.1.1 Message Structure

```json
{
  "message_type": "LEAGUE_ERROR",
  "error_code": "E012",
  "error_description": "AUTH_TOKEN_INVALID",
  "original_message_type": "LEAGUE_QUERY",
  "context": {
    "provided_token": "tok_invalid_xxx",
    "expected_format": "tok_{agent_id}_{hash}"
  }
}
```

#### 9.1.2 Field Specifications

- **error_code** (string, required): Standardized error code
  - Format: "E" + three digits (E001, E012, E021)
  - See error codes table in league-system-prd.md

- **error_description** (string, required): Error name
  - Human-readable error type
  - Examples: "AUTH_TOKEN_INVALID", "PLAYER_NOT_REGISTERED"

- **original_message_type** (string, required): Message type that caused error
  - Example: "LEAGUE_QUERY", "LEAGUE_REGISTER_REQUEST"

- **context** (object, optional): Additional debugging information
  - Contents vary by error type
  - Helps agent diagnose issue

#### 9.1.3 Common League Error Codes

- **E003:** MISSING_REQUIRED_FIELD - Mandatory field missing
- **E005:** PLAYER_NOT_REGISTERED - Player ID not found
- **E011:** AUTH_TOKEN_MISSING - Token not provided
- **E012:** AUTH_TOKEN_INVALID - Token invalid or expired
- **E018:** PROTOCOL_VERSION_MISMATCH - Unsupported protocol version
- **E019:** LATE_REGISTRATION - Registration after league start
- **E021:** INVALID_TIMESTAMP - Timestamp not in UTC

#### 9.1.4 Acceptance Criteria

- ✅ error_code is from official error catalog
- ✅ error_description clearly identifies problem
- ✅ original_message_type helps agent understand context
- ✅ context provides actionable debugging info

---

### 9.2 GAME_ERROR

**Direction:** Referee → Player
**Purpose:** Notify player of game-level error (timeout, invalid move, etc.)
**Expected Response:** Retry (if retryable) or accept failure

#### 9.2.1 Message Structure

**Timeout Error:**
```json
{
  "message_type": "GAME_ERROR",
  "match_id": "R1M1",
  "error_code": "E001",
  "error_description": "TIMEOUT_ERROR",
  "affected_player": "P02",
  "action_required": "CHOOSE_PARITY_RESPONSE",
  "retry_info": {
    "retry_count": 1,
    "max_retries": 3,
    "next_retry_at": "20250115T10:16:02Z"
  },
  "consequence": "Technical loss if max retries exceeded"
}
```

**Invalid Choice Error:**
```json
{
  "message_type": "GAME_ERROR",
  "match_id": "R1M1",
  "error_code": "E004",
  "error_description": "INVALID_PARITY_CHOICE",
  "affected_player": "P01",
  "action_required": "CHOOSE_PARITY_RESPONSE",
  "retry_info": {
    "retry_count": 1,
    "max_retries": 3,
    "time_remaining": 18.5
  },
  "context": {
    "invalid_choice": "Even",
    "valid_choices": ["even", "odd"]
  },
  "consequence": "Technical loss if valid choice not received before timeout"
}
```

#### 9.2.2 Field Specifications

- **match_id** (string, required): Match where error occurred
- **error_code** (string, required): Error code
- **error_description** (string, required): Error name

- **affected_player** (string, required): Player who caused/is affected by error
- **action_required** (string, required): What player needs to do
  - Example: "CHOOSE_PARITY_RESPONSE", "GAME_JOIN_ACK"

**retry_info** (object, optional): Retry information if applicable
- **retry_count** (integer): Current retry attempt (1, 2, or 3)
- **max_retries** (integer): Maximum attempts allowed (typically 3)
- **next_retry_at** (string, optional): UTC timestamp when next retry will be attempted
- **time_remaining** (float, optional): Seconds remaining in timeout window

- **context** (object, optional): Error-specific details
- **consequence** (string, required): What happens if error not resolved
  - Example: "Technical loss if max retries exceeded"

#### 9.2.3 Common Game Error Codes

- **E001:** TIMEOUT_ERROR - Response not received in time
- **E004:** INVALID_PARITY_CHOICE - Choice not "even" or "odd"
- **E009:** CONNECTION_ERROR - Network connection failed
- **E015:** MATCH_ID_MISMATCH - Match ID doesn't match

#### 9.2.4 Retry Logic

**Retryable Errors:**
- E001 (TIMEOUT_ERROR) - Max 3 retries, 2-second delay
- E009 (CONNECTION_ERROR) - Max 3 retries, 2-second delay

**Non-Retryable Errors:**
- E004 (INVALID_PARITY_CHOICE) - Can retry within timeout window, but no automatic retries
- E012 (AUTH_TOKEN_INVALID) - No retry (fix token first)

#### 9.2.5 Acceptance Criteria

- ✅ Sent immediately when error detected
- ✅ retry_info included for retryable errors
- ✅ consequence clearly states what happens if unresolved
- ✅ context provides debugging information
- ✅ Player can retry if within timeout window

---

## 10. Message Summary & Validation Rules

### 10.1 Complete Message Type Catalog

**Table: All 18 Message Types in Protocol v2.1**

| # | Message Type | Sender | Receiver | Purpose | Timeout |
|---|--------------|--------|----------|---------|---------|
| 1 | REFEREE_REGISTER_REQUEST | Referee | League | Register referee | 10s |
| 2 | REFEREE_REGISTER_RESPONSE | League | Referee | Confirm referee registration | N/A |
| 3 | LEAGUE_REGISTER_REQUEST | Player | League | Register player | 10s |
| 4 | LEAGUE_REGISTER_RESPONSE | League | Player | Confirm player registration | N/A |
| 5 | ROUND_ANNOUNCEMENT | League | All Players | Announce round start | N/A |
| 6 | ROUND_COMPLETED | League | All | Announce round completion | N/A |
| 7 | LEAGUE_COMPLETED | League | All | Announce tournament end | N/A |
| 8 | GAME_INVITATION | Referee | Player | Invite to match | 5s |
| 9 | GAME_JOIN_ACK | Player | Referee | Confirm arrival | 5s |
| 10 | CHOOSE_PARITY_CALL | Referee | Player | Request choice | 30s |
| 11 | CHOOSE_PARITY_RESPONSE | Player | Referee | Provide choice | 30s |
| 12 | GAME_OVER | Referee | Both Players | Notify match outcome | 5s |
| 13 | MATCH_RESULT_REPORT | Referee | League | Report result | 10s |
| 14 | LEAGUE_STANDINGS_UPDATE | League | All Players | Broadcast standings | N/A |
| 15 | LEAGUE_ERROR | League | Agent | League-level error | N/A |
| 16 | GAME_ERROR | Referee | Player | Game-level error | N/A |
| 17 | LEAGUE_QUERY | Player/Referee | League | Query information | 10s |
| 18 | LEAGUE_QUERY_RESPONSE | League | Player/Referee | Query response | N/A |

---

### 10.2 Mandatory Fields (All Messages)

**From Envelope (see league-system-prd.md):**
- `protocol`: Always "league.v2"
- `message_type`: One of the 18 types above
- `sender`: Format "type:id" (e.g., "player:P01")
- `timestamp`: ISO 8601 UTC format with 'Z' suffix
- `conversation_id`: Unique conversation identifier

**Additional Context Fields (when applicable):**
- `auth_token`: Required for all post-registration messages
- `match_id`: Required for all game-related messages
- `player_id`: Required when message is player-specific
- `league_id`: Required for league-wide messages

---

### 10.3 Allowed Values & Validation

**parity_choice:**
- **ONLY:** `"even"` or `"odd"` (lowercase, string type)
- **Invalid:** Any other value, case variation, or type

**status (registration responses):**
- **ONLY:** `"ACCEPTED"` or `"REJECTED"`

**status (game results):**
- **ONLY:** `"WIN"`, `"DRAW"`, or `"TECHNICAL_LOSS"`

**accept (game join acknowledgment):**
- **ONLY:** `true` or `false` (boolean type)

**query_type:**
- **ONLY:** `"GET_STANDINGS"`, `"GET_SCHEDULE"`, `"GET_NEXT_MATCH"`, `"GET_PLAYER_STATS"`

---

### 10.4 Time Format Requirements

**All timestamps must be ISO 8601 in UTC:**
```
Format: YYYY-MM-DDTHH:MM:SSZ
Example: 20250115T10:30:00Z
```

**Required suffix:** `Z` (indicating UTC)
**Alternative accepted:** `+00:00` (explicit UTC offset)
**Invalid:** Any other timezone offset (e.g., `+02:00`, `-05:00`)

---

### 10.5 Critical Validation Rules

**Rule 1: Case-Sensitive String Matching**
- `"even"` ≠ `"Even"` ≠ `"EVEN"`
- All protocol values are case-sensitive unless explicitly stated

**Rule 2: Type Validation**
- String fields must be strings (not integers, booleans, or null)
- Integer fields must be integers (not strings)
- Boolean fields must be booleans (not 0/1 or "true"/"false")

**Rule 3: Required Fields**
- Missing required field → error E003 (MISSING_REQUIRED_FIELD)
- Null value for required field → error E003

**Rule 4: Timeout Enforcement**
- Timeout measured from message send to response receive
- Timeout triggers retry logic (if applicable)
- Max retries exhausted → TECHNICAL_LOSS

**Rule 5: Match ID Consistency**
- All messages in one game must use same `match_id`
- Mismatch → error E015 (MATCH_ID_MISMATCH)

---

## 11. User Stories

### US-1: Send Registration Request
> **As a** player agent developer
> **I want to** send a correctly formatted LEAGUE_REGISTER_REQUEST
> **So that** my agent is accepted into the tournament
>
> **Acceptance Criteria:**
> - All required fields present
> - Field types correct (string, integer, etc.)
> - contact_endpoint is reachable
> - Response received within 10 seconds

### US-2: Respond to Game Invitation
> **As a** player agent
> **I want to** acknowledge game invitations within 5 seconds
> **So that** I don't forfeit matches due to timeout
>
> **Acceptance Criteria:**
> - GAME_JOIN_ACK sent within 5 seconds
> - accept field is boolean true
> - arrival_timestamp in correct UTC format

### US-3: Submit Valid Choice
> **As a** player agent
> **I want to** submit my parity choice in the exact required format
> **So that** my choice is accepted and I don't get validation errors
>
> **Acceptance Criteria:**
> - parity_choice is exactly "even" or "odd" (lowercase)
> - Type is string (not integer or boolean)
> - Response within 30 seconds

### US-4: Handle Error Messages
> **As a** player agent developer
> **I want to** receive clear error messages when I make mistakes
> **So that** I can quickly debug and fix my implementation
>
> **Acceptance Criteria:**
> - Error messages include error_code and error_description
> - context provides debugging information
> - retry_info indicates if retry is possible

### US-5: Query Tournament Information
> **As a** player agent
> **I want to** query standings and schedule information
> **So that** I can make strategic decisions
>
> **Acceptance Criteria:**
> - LEAGUE_QUERY sent with correct query_type
> - LEAGUE_QUERY_RESPONSE received within 10 seconds
> - data contains requested information

---

## 12. Acceptance Criteria

### 12.1 Message Structure Compliance
- ✅ All messages include mandatory envelope fields
- ✅ All messages use correct message_type value
- ✅ Field names match specification exactly (case-sensitive)
- ✅ Field types match specification (string, int, bool, object, array)
- ✅ Required fields are always present (never null or missing)

### 12.2 Registration Messages
- ✅ REFEREE_REGISTER_REQUEST includes all referee_meta fields
- ✅ LEAGUE_REGISTER_REQUEST includes all player_meta fields
- ✅ Responses include status ("ACCEPTED" or "REJECTED")
- ✅ If ACCEPTED: ID and auth_token provided
- ✅ If REJECTED: reason provided

### 12.3 Game Flow Messages
- ✅ GAME_INVITATION includes opponent_id and conversation_id
- ✅ GAME_JOIN_ACK includes boolean accept field
- ✅ CHOOSE_PARITY_RESPONSE includes exactly "even" or "odd"
- ✅ GAME_OVER includes choices, drawn_number, winner, reason

### 12.4 Result Messages
- ✅ MATCH_RESULT_REPORT includes score and details
- ✅ LEAGUE_STANDINGS_UPDATE sorted by rank
- ✅ Points calculated correctly (wins×3 + draws×1)

### 12.5 Error Messages
- ✅ LEAGUE_ERROR includes error_code, error_description, original_message_type
- ✅ GAME_ERROR includes affected_player, action_required, consequence
- ✅ retry_info included for retryable errors

### 12.6 Validation
- ✅ Invalid parity_choice rejected with E004 error
- ✅ Missing required fields rejected with E003 error
- ✅ Invalid timestamp format rejected with E021 error
- ✅ Timeout enforcement: response required within specified time

---

## 13. Success Metrics

### 13.1 Protocol Compliance
- **Message Format Compliance:** 100% of messages conform to specification
- **Validation Success Rate:** > 99% of messages pass validation (excluding intentional errors)
- **Field Type Errors:** < 1% (indicates good documentation/examples)

### 13.2 Error Recovery
- **Retry Success Rate:** > 80% of retryable errors succeed on retry
- **Timeout Rate:** < 5% of messages timeout (indicates healthy network/agents)
- **Invalid Choice Rate:** < 5% (decreases as students learn specification)

### 13.3 Communication Performance
- **Message Round-Trip Time:** < 500ms (same network)
- **Query Response Time:** < 1 second average
- **Standings Update Latency:** < 5 seconds after match

### 13.4 Student Success
- **Implementation Success:** > 95% of students correctly implement all message types
- **First-Try Success:** > 80% of registration attempts succeed on first try
- **Error Resolution Time:** < 30 minutes average (from error to fix)

---

## 14. Technical Constraints

### 14.1 Message Size Limits
- **Maximum message size:** 10 KB (typical: < 2 KB)
- **Maximum array length (standings):** 100 elements
- **Maximum string length (display_name):** 50 characters

### 14.2 Timeout Limits (Hard Requirements)
- REFEREE_REGISTER: 10 seconds
- LEAGUE_REGISTER: 10 seconds
- GAME_JOIN_ACK: 5 seconds
- CHOOSE_PARITY: 30 seconds
- GAME_OVER acknowledgment: 5 seconds (best-effort)
- MATCH_RESULT_REPORT: 10 seconds
- LEAGUE_QUERY: 10 seconds
- All others: 10 seconds (default)

### 14.3 Retry Policy (Fixed)
- **Max retries:** 3
- **Delay between retries:** 2 seconds
- **Retryable errors:** E001 (timeout), E009 (connection)
- **Non-retryable errors:** E004 (invalid choice), E012 (invalid token)

### 14.4 Field Validation
- **Strings:** UTF-8 encoding
- **Timestamps:** ISO 8601 with 'Z' suffix (UTC mandatory)
- **Booleans:** true/false (not 0/1 or "true"/"false")
- **Integers:** Signed 32-bit (-2³¹ to 2³¹-1)

### 14.5 Backward Compatibility
- **Message types:** Never remove or rename existing types
- **Fields:** Can add optional fields, never remove required fields
- **Values:** Can add new allowed values, never remove existing ones
- **Protocol version:** MAJOR.MINOR.PATCH (current: 2.1.0)

---

**Document Status:** DRAFT - Pending Review
**Next Review Date:** 2025-12-27
**Approvers:** Course Instructor, Technical Lead, Protocol Designer

**CRITICAL NOTE:** This specification is the single source of truth for message formats. All student implementations MUST conform exactly to avoid communication failures.
