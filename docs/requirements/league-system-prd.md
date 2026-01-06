# Product Requirements Document (PRD)
# League Management System - General League Protocol v2.1

**Document Version:** 1.0
**Date:** 2025-12-20
**Status:** Draft
**Product Owner:** AI Development Course Team
**Target Release:** Phase 1 - Foundation

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Product Vision](#product-vision)
3. [User Personas](#user-personas)
4. [Feature Requirements](#feature-requirements)
5. [User Stories](#user-stories)
6. [Acceptance Criteria](#acceptance-criteria)
7. [Success Metrics](#success-metrics)
8. [Technical Constraints](#technical-constraints)
9. [Dependencies](#dependencies)
10. [Timeline & Milestones](#timeline--milestones)
11. [Risk Assessment](#risk-assessment)

---

## 1. Executive Summary

### 1.1 Problem Statement
The league system needs a standardized protocol that enables autonomous agents developed by different students (potentially in different programming languages) to participate in competitive game tournaments. The current lack of a unified communication protocol prevents interoperability and scalable tournament management.

### 1.2 Solution Overview
Implement a **General League Protocol v2.1** - a three-layer architecture (League, Referee, Player) with standardized message formats, authentication, timeout handling, and error recovery. The protocol uses MCP (Model Context Protocol) servers with JSON-RPC 2.0 communication to ensure language-agnostic agent participation.

### 1.3 Key Benefits
- **Language Agnostic**: Students can implement agents in any language
- **Scalable**: Supports multiple concurrent games and referees
- **Reliable**: Built-in timeout handling, retry logic, and error recovery
- **Extensible**: Game-agnostic design allows adding new game types
- **Traceable**: Comprehensive logging with conversation IDs and timestamps
- **Secure**: Token-based authentication prevents agent impersonation

---

## 2. Product Vision

### 2.1 Vision Statement
*"Enable a fair, automated, and scalable competitive environment where AI agents developed by students can compete in strategic games, fostering learning through real-world multi-agent system design."*

### 2.2 Strategic Goals
1. **Accessibility**: Lower barrier to entry - any student with basic programming skills can participate
2. **Fairness**: Uniform protocol ensures no agent has protocol-level advantages
3. **Reliability**: System handles failures gracefully with automatic recovery
4. **Educational Value**: Students learn distributed systems, protocol design, and game theory
5. **Scalability**: System supports 50+ concurrent players and 10+ simultaneous games

### 2.3 Out of Scope (v2.1)
- Web-based UI for tournament visualization (future: v2.2)
- Real-time spectator mode (future: v2.3)
- Cross-league tournaments (future: v3.0)
- Machine learning analytics dashboard (future: v2.4)

---

## 3. User Personas

### 3.1 Persona: Student Developer (Primary User)
**Name:** Alex - Computer Science Student
**Goals:**
- Implement a competitive AI agent for the league
- Learn about multi-agent systems and protocol design
- Rank competitively in tournament standings
- Debug agent behavior efficiently

**Pain Points:**
- Unclear protocol specifications lead to implementation errors
- Timeout errors cause match losses without clear debugging info
- Difficulty testing agent in isolation before tournament
- Authentication token management confusion

**Success Criteria:**
- Agent successfully registers and participates in all scheduled matches
- Clear error messages enable quick debugging
- Agent responds within timeout constraints
- Achieves target win rate based on strategy

---

### 3.2 Persona: Course Instructor (Secondary User)
**Name:** Dr. Smith - AI Course Instructor
**Goals:**
- Run automated tournaments for class assignments
- Monitor student agent performance
- Ensure fair competition and rule compliance
- Generate performance reports for grading

**Pain Points:**
- Manual tournament management is time-consuming
- Difficult to detect rule violations or cheating
- Hard to identify technical issues vs strategic failures
- Limited visibility into agent decision-making

**Success Criteria:**
- Tournaments run automatically without manual intervention
- Complete audit trail of all agent actions
- Clear distinction between technical failures and strategic losses
- Exportable performance metrics for grading

---

### 3.3 Persona: System Administrator (Tertiary User)
**Name:** Sam - DevOps Engineer
**Goals:**
- Deploy and maintain league infrastructure
- Monitor system health and performance
- Handle scaling for large tournaments
- Debug production issues quickly

**Pain Points:**
- Unclear system state during failures
- Difficult to correlate logs across distributed components
- Scaling challenges with many concurrent games
- Authentication token lifecycle management

**Success Criteria:**
- Centralized logging with correlation IDs
- Health check endpoints for all components
- Horizontal scalability for referees and players
- Automated recovery from transient failures

---

## 4. Feature Requirements

### 4.1 Epic 1: Three-Layer Architecture

#### 4.1.1 Feature: League Manager Layer
**Priority:** P0 (Must Have)
**Description:** Central authority managing tournament lifecycle, player registration, scheduling, and standings.

**Key Capabilities:**
- Register and authenticate referees
- Register and authenticate players
- Generate round-robin tournament schedules
- Track and publish real-time standings
- Handle multi-round tournaments
- Provide league information API

**Port Assignment:** 8000 (fixed)

---

#### 4.1.2 Feature: Referee Layer
**Priority:** P0 (Must Have)
**Description:** Game orchestrators that manage individual matches, validate moves, and report results.

**Key Capabilities:**
- Register with League Manager
- Invite players to matches
- Manage game state and turns
- Validate move legality
- Enforce timeout constraints
- Determine and report match outcomes
- Handle player disconnections/failures

**Port Assignment:** 8001-8010 (supports up to 10 concurrent referees)

---

#### 4.1.3 Feature: Player Agent Layer
**Priority:** P0 (Must Have)
**Description:** Student-implemented autonomous agents that compete in games.

**Key Capabilities:**
- Register with League Manager
- Accept/reject game invitations
- Choose moves within timeout limits
- Receive and process match results
- Maintain internal game history and strategy state
- Respond to protocol queries

**Port Assignment:** 8101-8150 (supports up to 50 players)

---

### 4.2 Epic 2: Protocol Message System

#### 4.2.1 Feature: Message Envelope (Wrapper)
**Priority:** P0 (Must Have)
**Description:** Standardized message wrapper ensuring consistency across all protocol messages.

**Required Fields:**
- `protocol`: Version string (fixed: "league.v2")
- `message_type`: Message type identifier (e.g., "GAME_INVITATION")
- `sender`: Sender identifier in format `type:id` (e.g., "referee:REF01")
- `timestamp`: ISO 8601 UTC timestamp with 'Z' suffix
- `conversation_id`: Unique conversation identifier for tracing

**Optional Fields (context-dependent):**
- `auth_token`: Authentication token (mandatory post-registration)
- `league_id`: League identifier
- `round_id`: Round number
- `match_id`: Match identifier

**Validation Rules:**
- Timestamp MUST be in UTC/GMT timezone (enforced)
- Missing required fields → error E003
- Invalid timestamp format → error E021
- Missing auth_token (when required) → error E011

---

#### 4.2.2 Feature: UTC/GMT Timezone Enforcement
**Priority:** P0 (Must Have)
**Description:** Mandatory UTC timezone for all timestamps to ensure global consistency.

**Acceptance Criteria:**
- ✅ Timestamps with 'Z' suffix accepted: `20250115T10:30:00Z`
- ✅ Timestamps with `+00:00` offset accepted: `20250115T10:30:00+00:00`
- ❌ Local timezone offsets rejected: `20250115T10:30:00+02:00` → E021 error
- ❌ Timestamps without timezone rejected: `20250115T10:30:00` → E021 error

---

#### 4.2.3 Feature: Sender Identification Format
**Priority:** P0 (Must Have)
**Description:** Standardized sender field format for clear message origin tracking.

**Format Specification:**
- League Manager: `league_manager` (no prefix)
- Referee: `referee:<referee_id>` (e.g., `referee:REF01`)
- Player: `player:<player_id>` (e.g., `player:P01`)

**Use Cases:**
- Message routing and filtering
- Authorization validation
- Audit trail logging
- Debugging message flows

---

### 4.3 Epic 3: Registration & Authentication

#### 4.3.1 Feature: Referee Registration
**Priority:** P0 (Must Have)
**Description:** Referees register with League Manager before officiating games.

**User Story:**
> **As a** referee agent
> **I want to** register with the League Manager
> **So that** I can be assigned to officiate matches in the tournament

**Message Flow:**
```
Referee → League Manager: REFEREE_REGISTER_REQUEST
{
  "referee_meta": {
    "display_name": "Referee Alpha",
    "version": "1.0.0",
    "protocol_version": "2.1.0",
    "supported_games": ["even_odd", "tic_tac_toe"],
    "max_concurrent_games": 5
  }
}

League Manager → Referee: REFEREE_REGISTER_RESPONSE
{
  "status": "ACCEPTED" | "REJECTED",
  "referee_id": "REF01",
  "auth_token": "tok_ref01_abc123...",
  "league_id": "league_2025_even_odd"
}
```

**Acceptance Criteria:**
- ✅ Referee sends registration request with metadata
- ✅ League Manager validates protocol version compatibility (≥2.0.0)
- ✅ League Manager assigns unique `referee_id`
- ✅ League Manager generates secure `auth_token`
- ✅ Response received within 10 seconds (timeout)
- ✅ Rejected if protocol version incompatible (E018 error)
- ✅ Referee stores `auth_token` for all future messages

**Timeout:** 10 seconds

---

#### 4.3.2 Feature: Player Registration
**Priority:** P0 (Must Have)
**Description:** Players register with League Manager to participate in tournament.

**User Story:**
> **As a** student developer
> **I want to** register my agent with the league
> **So that** my agent can participate in scheduled matches

**Message Flow:**
```
Player → League Manager: LEAGUE_REGISTER_REQUEST
{
  "player_meta": {
    "display_name": "Agent Alpha",
    "version": "1.0.0",
    "protocol_version": "2.1.0",
    "game_types": ["even_odd"],
    "contact_email": "student@university.edu"
  }
}

League Manager → Player: LEAGUE_REGISTER_RESPONSE
{
  "status": "ACCEPTED" | "REJECTED",
  "player_id": "P01",
  "auth_token": "tok_p01_abc123def456...",
  "league_id": "league_2025_even_odd",
  "rejection_reason": null
}
```

**Acceptance Criteria:**
- ✅ Player sends registration request with metadata
- ✅ League Manager validates protocol version (2.0.0 - 2.1.0 supported)
- ✅ League Manager assigns unique sequential `player_id` (P01, P02, ...)
- ✅ League Manager generates cryptographically secure `auth_token`
- ✅ Response received within 10 seconds
- ✅ Duplicate registration rejected with clear error message
- ✅ Player stores `auth_token` for all future protocol messages
- ✅ Registration before league start only

**Edge Cases:**
- Late registration (after league start) → rejected with E019 error
- Duplicate `display_name` → allowed (disambiguated by `player_id`)
- Protocol version < 2.0.0 → rejected with E018 error

**Timeout:** 10 seconds

---

#### 4.3.3 Feature: Token-Based Authentication
**Priority:** P0 (Must Have)
**Description:** All post-registration messages must include valid `auth_token`.

**User Story:**
> **As the** League Manager
> **I want to** validate authentication tokens on every message
> **So that** agents cannot impersonate other players

**Token Lifecycle:**
1. **Generation**: Upon successful registration
2. **Storage**: Agent stores securely (environment variable recommended)
3. **Usage**: Included in every message's `auth_token` field
4. **Validation**: League Manager/Referee validates before processing
5. **Expiration**: Valid for entire league duration (no rotation in v2.1)

**Acceptance Criteria:**
- ✅ Token format: `tok_{type}_{id}_{random_64chars}`
- ✅ Missing token → E011 error (AUTH_TOKEN_MISSING)
- ✅ Invalid token → E012 error (AUTH_TOKEN_INVALID)
- ✅ Mismatched token (wrong player) → E012 error
- ✅ Token validated on every message (except registration)
- ✅ Token generation uses cryptographically secure random

**Security Considerations:**
- Tokens generated using `secrets` module (Python) or equivalent
- Minimum 64 characters of randomness
- No token reuse across leagues
- Token invalidated if player suspended/banned

---

### 4.4 Epic 4: Game Scheduling & Flow

#### 4.4.1 Feature: Round-Robin Schedule Generation
**Priority:** P0 (Must Have)
**Description:** League Manager generates fair round-robin schedule where every player plays every other player exactly once.

**User Story:**
> **As the** League Manager
> **I want to** generate a round-robin schedule
> **So that** every player competes fairly against all opponents

**Algorithm Requirements:**
- **Input**: List of N registered players
- **Output**: M rounds, where M = N - 1 (for even N) or M = N (for odd N)
- **Constraint**: Each player plays exactly once per round
- **Constraint**: No player plays themselves
- **Bye Handling**: If N is odd, one player gets a bye each round (rotates)

**Example (4 players: P01, P02, P03, P04):**
```
Round 1:
  Match R1M1: P01 vs P02 (Referee: REF01)
  Match R1M2: P03 vs P04 (Referee: REF02)

Round 2:
  Match R2M1: P01 vs P03 (Referee: REF01)
  Match R2M2: P02 vs P04 (Referee: REF02)

Round 3:
  Match R3M1: P01 vs P04 (Referee: REF01)
  Match R3M2: P02 vs P03 (Referee: REF02)
```

**Acceptance Criteria:**
- ✅ Each player plays N-1 matches (against every other player)
- ✅ Matches distributed evenly across rounds
- ✅ Referee assignment balanced (if multiple referees available)
- ✅ Bye handling for odd number of players
- ✅ Schedule generated within 5 seconds for up to 50 players
- ✅ Match IDs follow pattern: `R{round_id}M{match_num}`

**Performance Target:**
- 10 players: < 1 second
- 50 players: < 5 seconds
- 100 players: < 15 seconds

---

#### 4.4.2 Feature: Round Announcement
**Priority:** P0 (Must Have)
**Description:** League Manager announces round start with full match schedule.

**User Story:**
> **As a** player agent
> **I want to** receive round announcements
> **So that** I know when my matches are scheduled

**Message Flow:**
```
League Manager → All Players & Referees: ROUND_ANNOUNCEMENT
{
  "round_id": 1,
  "matches": [
    {
      "match_id": "R1M1",
      "player1_id": "P01",
      "player2_id": "P02",
      "referee_id": "REF01",
      "scheduled_start": "20250115T11:00:00Z"
    },
    {
      "match_id": "R1M2",
      "player3_id": "P03",
      "player4_id": "P04",
      "referee_id": "REF02",
      "scheduled_start": "20250115T11:00:00Z"
    }
  ],
  "round_deadline": "20250115T12:00:00Z"
}
```

**Acceptance Criteria:**
- ✅ Broadcast to all registered players and referees
- ✅ Includes complete match schedule with referee assignments
- ✅ Scheduled start times coordinated (avoid referee overload)
- ✅ Players can plan strategy based on upcoming opponent
- ✅ Announcement sent at least 60 seconds before first match
- ✅ Round deadline set with buffer for all match timeouts

---

#### 4.4.3 Feature: Game Invitation & Acknowledgment
**Priority:** P0 (Must Have)
**Description:** Referee invites players to match; players must acknowledge within timeout.

**User Story:**
> **As a** referee
> **I want to** invite players to a match
> **So that** I can confirm both players are ready before starting

**Message Flow:**
```
Referee → Player: GAME_INVITATION
{
  "match_id": "R1M1",
  "game_type": "even_odd",
  "opponent_id": "P02",
  "player_role": "player1",
  "max_response_time": 5
}

Player → Referee: GAME_JOIN_ACK
{
  "match_id": "R1M1",
  "status": "ACCEPTED" | "REJECTED",
  "ready": true
}
```

**Acceptance Criteria:**
- ✅ Referee sends invitation to both players
- ✅ Player responds within 5 seconds (timeout)
- ✅ Player can reject (e.g., not ready, error state)
- ✅ If rejected → player forfeits match (TECHNICAL_LOSS)
- ✅ If timeout → player forfeits match (TECHNICAL_LOSS)
- ✅ Both players must accept before game starts
- ✅ Rejection reason logged for debugging

**Timeout:** 5 seconds
**Retry Policy:** No retries for invitation (immediate forfeit)

---

### 4.5 Epic 5: Game Execution

#### 4.5.1 Feature: Game State Management (Referee)
**Priority:** P0 (Must Have)
**Description:** Referee maintains authoritative game state throughout match.

**User Story:**
> **As a** referee
> **I want to** maintain the single source of truth for game state
> **So that** there's no ambiguity or dispute about match status

**Game States:**
- `PENDING`: Match scheduled but not started
- `INVITING`: Sending invitations to players
- `COLLECTING_CHOICES`: Waiting for player moves
- `EVALUATING`: Determining winner
- `COMPLETED`: Match finished, result determined
- `ABORTED`: Match cancelled due to errors

**State Transitions:**
```
PENDING → INVITING → COLLECTING_CHOICES → EVALUATING → COMPLETED
                ↓             ↓
             ABORTED       ABORTED
```

**Acceptance Criteria:**
- ✅ Referee stores complete game state
- ✅ State transitions follow defined flow
- ✅ Invalid transitions rejected
- ✅ State persisted for recovery
- ✅ State included in all messages for player awareness

---

#### 4.5.2 Feature: Move Collection with Timeout
**Priority:** P0 (Must Have)
**Description:** Referee collects player moves (choices) with strict timeout enforcement.

**User Story:**
> **As a** referee
> **I want to** collect player moves with timeout enforcement
> **So that** slow or unresponsive players don't stall the tournament

**Message Flow (Even/Odd Game):**
```
Referee → Player: CHOOSE_PARITY
{
  "match_id": "R1M1",
  "opponent_id": "P02",
  "standings": [...],
  "game_history": [...]
}

Player → Referee: PARITY_CHOICE
{
  "match_id": "R1M1",
  "choice": "even" | "odd",
  "reasoning": "Opponent tends to pick even"
}
```

**Timeout Handling:**
1. Referee sends `CHOOSE_PARITY` to both players
2. Waits up to 30 seconds for each response
3. If player responds in time → choice recorded
4. If player times out → retry up to 3 times (2s delay)
5. If max retries exhausted → TECHNICAL_LOSS for that player

**Acceptance Criteria:**
- ✅ Timeout enforced at 30 seconds
- ✅ Retry logic: 3 attempts, 2-second delay
- ✅ Simultaneous move collection (no sequential advantage)
- ✅ Choices remain hidden until both collected
- ✅ Invalid choices (not "even"/"odd") → validation error
- ✅ After timeout → GAME_ERROR sent to player
- ✅ Technical loss recorded in match result

**Timeout:** 30 seconds
**Retry Policy:** 3 attempts, 2-second delay, E001 error

---

#### 4.5.3 Feature: Move Validation
**Priority:** P0 (Must Have)
**Description:** Referee validates all moves according to game rules.

**User Story:**
> **As a** referee
> **I want to** validate player moves
> **So that** only legal moves are accepted

**Validation Rules (Even/Odd Game):**
- Choice must be exactly "even" or "odd" (case-sensitive)
- Choice must be a string, not integer or boolean
- Match ID in response must match request
- Response must include valid `auth_token`

**Acceptance Criteria:**
- ✅ Invalid choice → E004 error (INVALID_PARITY_CHOICE)
- ✅ Mismatched match_id → E015 error
- ✅ Missing required fields → E003 error
- ✅ Validation errors allow retry (within timeout window)
- ✅ Clear error messages for debugging
- ✅ Validation logged for audit

**Error Responses:**
```json
{
  "message_type": "GAME_ERROR",
  "error_code": "E004",
  "error_name": "INVALID_PARITY_CHOICE",
  "error_description": "Choice must be 'even' or 'odd', got 'maybe'",
  "retryable": true,
  "retry_count": 1,
  "max_retries": 3
}
```

---

#### 4.5.4 Feature: Winner Determination
**Priority:** P0 (Must Have)
**Description:** Referee determines match outcome based on game rules and random draw.

**User Story:**
> **As a** referee
> **I want to** determine match winners fairly
> **So that** players trust the competition integrity

**Even/Odd Game Logic:**
1. Collect both player choices (even/odd)
2. Generate random integer between 1-10 (inclusive)
3. Determine winner:
   - If number is even (2,4,6,8,10) → player who chose "even" wins
   - If number is odd (1,3,5,7,9) → player who chose "odd" wins
   - If both chose same → tie
4. Record result

**Randomness Requirements:**
- Use cryptographically secure random (not pseudo-random)
- Uniform distribution (each number 1-10 equally likely)
- Random seed must NOT be predictable
- Log random number for audit/dispute resolution

**Acceptance Criteria:**
- ✅ Random number generation is cryptographically secure
- ✅ Winner determination follows game rules exactly
- ✅ Tie handling: both players get 1 point
- ✅ Technical loss: opponent gets 3 points, failed player gets 0
- ✅ Result logged with timestamp, choices, random number
- ✅ Statistical test: 10,000 games → 50% even, 50% odd (±2%)

---

### 4.6 Epic 6: Result Reporting & Standings

#### 4.6.1 Feature: Match Result Notification
**Priority:** P0 (Must Have)
**Description:** Referee notifies players of match outcome.

**User Story:**
> **As a** player agent
> **I want to** receive match results
> **So that** I can update my strategy and learn from outcomes

**Message Flow:**
```
Referee → Both Players: GAME_OVER
{
  "match_id": "R1M1",
  "winner_id": "P01" | null,
  "result_type": "WIN" | "LOSS" | "TIE" | "TECHNICAL_LOSS",
  "drawn_number": 7,
  "choices": {
    "P01": "odd",
    "P02": "even"
  },
  "points_awarded": {
    "P01": 3,
    "P02": 0
  },
  "game_state": "COMPLETED"
}

Player → Referee: GAME_OVER_ACK
{
  "match_id": "R1M1",
  "acknowledged": true
}
```

**Acceptance Criteria:**
- ✅ Both players receive identical result notification
- ✅ Includes all relevant data: winner, choices, random number, points
- ✅ Result_type clearly indicates outcome
- ✅ Player acknowledges receipt within 5 seconds
- ✅ If acknowledgment timeout → logged but doesn't affect result
- ✅ Result stored in player's game history (player responsibility)

**Timeout:** 5 seconds (for acknowledgment)

---

#### 4.6.2 Feature: Result Reporting to League
**Priority:** P0 (Must Have)
**Description:** Referee reports match result to League Manager for standings update.

**User Story:**
> **As a** referee
> **I want to** report match results to the League Manager
> **So that** standings are updated accurately and in real-time

**Message Flow:**
```
Referee → League Manager: MATCH_RESULT_REPORT
{
  "match_id": "R1M1",
  "round_id": 1,
  "game_type": "even_odd",
  "players": {
    "P01": {
      "choice": "odd",
      "result": "WIN",
      "points": 3
    },
    "P02": {
      "choice": "even",
      "result": "LOSS",
      "points": 0
    }
  },
  "drawn_number": 7,
  "timestamp": "20250115T11:05:23Z",
  "referee_signature": "sig_ref01_abc..."
}

League Manager → Referee: MATCH_RESULT_ACK
{
  "match_id": "R1M1",
  "status": "RECORDED",
  "standings_updated": true
}
```

**Acceptance Criteria:**
- ✅ Report sent immediately after match completion
- ✅ Includes complete match data for audit trail
- ✅ League Manager validates referee signature (auth_token)
- ✅ Duplicate reports detected and ignored (idempotency)
- ✅ Response received within 10 seconds
- ✅ Retry on failure: 3 attempts, exponential backoff
- ✅ Critical path: standings update blocks next round announcement

**Timeout:** 10 seconds
**Retry Policy:** 3 attempts, exponential backoff (2s, 4s, 8s)

---

#### 4.6.3 Feature: Standings Calculation & Publication
**Priority:** P0 (Must Have)
**Description:** League Manager calculates and publishes updated standings after each match.

**User Story:**
> **As a** student developer
> **I want to** see current tournament standings
> **So that** I know my ranking and can adjust my strategy

**Scoring System:**
- **Win**: 3 points
- **Tie**: 1 point
- **Loss**: 0 points
- **Technical Loss**: 0 points (counts as loss in record)

**Ranking Tiebreakers (in order):**
1. Total points (descending)
2. Head-to-head record (if applicable)
3. Win percentage (wins / total games)
4. Alphabetical by player_id

**Standings Data Structure:**
```json
{
  "message_type": "STANDINGS_UPDATE",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "last_updated": "20250115T11:06:00Z",
  "standings": [
    {
      "rank": 1,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "wins": 2,
      "losses": 0,
      "ties": 1,
      "points": 7,
      "games_played": 3,
      "win_rate": 0.667
    },
    ...
  ]
}
```

**Acceptance Criteria:**
- ✅ Standings updated within 5 seconds of receiving match result
- ✅ Broadcast to all players after each match
- ✅ Accurate point calculation (no rounding errors)
- ✅ Tiebreaker logic applied correctly
- ✅ Historical standings preserved (for each round)
- ✅ Includes additional stats: games_played, win_rate
- ✅ Standings accessible via API query anytime

**Performance Target:**
- Update latency < 5 seconds for 50 players
- Query response < 1 second

---

### 4.7 Epic 7: Error Handling & Recovery

#### 4.7.1 Feature: Error Message Structure
**Priority:** P0 (Must Have)
**Description:** Standardized error message format for consistent error handling.

**Error Types:**
1. **LEAGUE_ERROR**: League-level errors (from League Manager)
2. **GAME_ERROR**: Game-level errors (from Referee)

**Error Message Structure:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "20250115T10:31:00Z",
  "match_id": "R1M1",
  "player_id": "P01",
  "error_code": "E001",
  "error_name": "TIMEOUT_ERROR",
  "error_description": "Response not received within 30 seconds",
  "game_state": "COLLECTING_CHOICES",
  "retryable": true,
  "retry_count": 1,
  "max_retries": 3,
  "context": {
    "elapsed_time": 30.5,
    "expected_message": "PARITY_CHOICE"
  }
}
```

**Acceptance Criteria:**
- ✅ All errors include error_code, error_name, error_description
- ✅ Retryable flag indicates if retry is allowed
- ✅ Context object provides debugging details
- ✅ Game state included for player awareness
- ✅ Retry count tracking for retry limit enforcement

---

#### 4.7.2 Feature: Error Codes & Catalog
**Priority:** P0 (Must Have)
**Description:** Comprehensive error code catalog for all failure scenarios.

**Error Code Categories:**

**Connection & Timeout Errors (E001-E010):**
- `E001`: TIMEOUT_ERROR - Response not received in time
- `E009`: CONNECTION_ERROR - Network connection failed

**Authentication & Authorization Errors (E011-E020):**
- `E011`: AUTH_TOKEN_MISSING - Token not provided
- `E012`: AUTH_TOKEN_INVALID - Token invalid or expired
- `E018`: PROTOCOL_VERSION_MISMATCH - Unsupported protocol version
- `E019`: LATE_REGISTRATION - Registration after league start

**Validation Errors (E003-E008):**
- `E003`: MISSING_REQUIRED_FIELD - Mandatory field missing
- `E004`: INVALID_PARITY_CHOICE - Choice not "even" or "odd"
- `E005`: PLAYER_NOT_REGISTERED - Player ID not found
- `E015`: MATCH_ID_MISMATCH - Match ID doesn't match

**Timestamp Errors (E021-E025):**
- `E021`: INVALID_TIMESTAMP - Timestamp not in UTC or invalid format

**Acceptance Criteria:**
- ✅ Each error code has unique number, name, description
- ✅ Error codes documented in protocol specification
- ✅ Agents can programmatically handle errors by code
- ✅ Error descriptions are human-readable for debugging
- ✅ Error codes never change (backwards compatibility)

---

#### 4.7.3 Feature: Retry Policy & Logic
**Priority:** P0 (Must Have)
**Description:** Automated retry logic for transient failures.

**Retry Policy:**
- **Max Attempts**: 3
- **Delay Between Attempts**: 2 seconds (fixed, not exponential for v2.1)
- **Retryable Errors**: E001 (timeout), E009 (connection)
- **Non-Retryable Errors**: E004 (invalid choice), E012 (invalid token)

**Retry Flow:**
```
Attempt 1 → Failure (E001) → Wait 2s
Attempt 2 → Failure (E001) → Wait 2s
Attempt 3 → Failure (E001) → Give Up → TECHNICAL_LOSS
```

**Acceptance Criteria:**
- ✅ Retry only for retryable errors
- ✅ Max 3 attempts enforced
- ✅ 2-second delay between attempts
- ✅ Retry count incremented and tracked
- ✅ After max retries → final error sent
- ✅ Player declared TECHNICAL_LOSS after exhaustion
- ✅ All retry attempts logged for debugging

**Edge Cases:**
- Retry succeeds on attempt 2 → game continues normally
- Different errors on different attempts → last error reported
- Player responds during retry delay → response accepted immediately

---

### 4.8 Epic 8: Agent Lifecycle & State Management

#### 4.8.1 Feature: Agent State Machine
**Priority:** P0 (Must Have)
**Description:** Defined agent lifecycle states with clear transition rules.

**Agent States:**
- `INIT`: Agent started but not registered
- `REGISTERED`: Successfully registered, has auth_token
- `ACTIVE`: Participating in matches
- `SUSPENDED`: Temporarily suspended (e.g., repeated timeouts)
- `SHUTDOWN`: Agent terminated or banned

**State Transitions:**
```
INIT → REGISTERED → ACTIVE
                ↓      ↓
            SUSPENDED  SHUTDOWN
                ↑
             (recover)
```

**Transition Triggers:**
- `register` → INIT to REGISTERED
- `league_start` → REGISTERED to ACTIVE
- `timeout (3x in row)` → ACTIVE to SUSPENDED
- `timeout recovery` → SUSPENDED to ACTIVE
- `league_end` → ACTIVE to SHUTDOWN
- `max_failures (10)` → ACTIVE to SHUTDOWN
- `critical_error` → any state to SHUTDOWN

**Acceptance Criteria:**
- ✅ Agent state persisted in League Manager database
- ✅ State transitions logged with timestamp and reason
- ✅ Players can query their current state
- ✅ Suspended agents can recover (manual or automatic)
- ✅ Shutdown agents cannot re-enter (must re-register)
- ✅ State included in standings for transparency

---

#### 4.8.2 Feature: Suspension & Recovery
**Priority:** P1 (Should Have)
**Description:** Temporary suspension for agents with transient issues.

**Suspension Triggers:**
- 3 consecutive timeouts
- 5 connection errors in 10 minutes
- Repeated invalid moves (5 validation errors)

**Recovery Process:**
1. Agent state set to SUSPENDED
2. League Manager sends SUSPENSION_NOTICE
3. Agent has 5 minutes to recover (health check)
4. If health check passes → state set to ACTIVE
5. If health check fails → state set to SHUTDOWN

**Acceptance Criteria:**
- ✅ Clear suspension criteria
- ✅ Suspension notice sent to agent
- ✅ Recovery window: 5 minutes
- ✅ Health check: simple ping-pong message
- ✅ Suspended agents don't participate in matches
- ✅ Standings show suspended status
- ✅ Auto-recovery if health check passes

---

### 4.9 Epic 9: Protocol Compatibility & Versioning

#### 4.9.1 Feature: Protocol Version Declaration
**Priority:** P0 (Must Have)
**Description:** Agents declare supported protocol version during registration.

**Version Format:** Semantic versioning (MAJOR.MINOR.PATCH)
- Example: `2.1.0`

**Compatibility Rules:**
- **Current Version**: 2.1.0
- **Minimum Supported**: 2.0.0
- **Major version mismatch** → rejected (e.g., v1.x.x)
- **Minor version delta** → allowed (e.g., 2.0.0 agent in 2.1.0 league)
- **Patch version** → ignored (backwards compatible)

**Acceptance Criteria:**
- ✅ Version declared in registration request
- ✅ League Manager validates compatibility
- ✅ Incompatible versions rejected with E018 error
- ✅ Error message includes required version range
- ✅ Version stored in player profile

**Example Rejection:**
```json
{
  "message_type": "LEAGUE_ERROR",
  "error_code": "E018",
  "error_name": "PROTOCOL_VERSION_MISMATCH",
  "error_description": "Agent protocol version 1.5.0 not supported. Required: 2.0.0 - 2.1.0",
  "context": {
    "agent_version": "1.5.0",
    "min_supported": "2.0.0",
    "current": "2.1.0"
  }
}
```

---

### 4.10 Epic 10: Audit & Logging

#### 4.10.1 Feature: Conversation ID Tracking
**Priority:** P0 (Must Have)
**Description:** Unique conversation IDs for tracing multi-message interactions.

**User Story:**
> **As a** system administrator
> **I want to** trace all messages in a conversation
> **So that** I can debug issues across multiple message exchanges

**Conversation ID Format:**
- Format: `conv{round_id}m{match_id}{random}`
- Example: `convr1m1001`
- Generated by: Referee (for game conversations)

**Scope:**
- Single conversation = invitation → moves → result
- Same conversation_id in all messages for one match
- Different matches = different conversation_ids

**Acceptance Criteria:**
- ✅ Conversation ID generated at invitation time
- ✅ All match-related messages include same conversation_id
- ✅ Enables log correlation across distributed components
- ✅ Stored with match result for audit trail
- ✅ Queryable for debugging disputes

---

#### 4.10.2 Feature: Comprehensive Logging
**Priority:** P0 (Must Have)
**Description:** Structured logging for all protocol events.

**Log Levels:**
- `DEBUG`: Message payloads, state transitions
- `INFO`: Match start/end, registrations
- `WARNING`: Retry attempts, validation warnings
- `ERROR`: Failures, timeouts, invalid messages
- `CRITICAL`: System failures, security violations

**Required Log Fields:**
- Timestamp (UTC)
- Component (league/referee/player)
- Log level
- Message type
- Conversation ID (if applicable)
- Player/Referee ID
- Error code (if error)
- Full message payload (DEBUG level)

**Acceptance Criteria:**
- ✅ All components use structured logging (JSON format)
- ✅ Logs include all required fields
- ✅ Sensitive data (tokens) redacted in logs
- ✅ Centralized log aggregation (future: ELK stack)
- ✅ Log retention: 30 days minimum
- ✅ Queryable by conversation_id, player_id, match_id

---

## 5. User Stories (Consolidated)

### 5.1 Student Developer Stories

**US-1: Register Agent**
> **As a** student developer
> **I want to** register my agent with the league
> **So that** it can participate in the tournament
> **Acceptance Criteria:** Agent receives player_id and auth_token within 10 seconds

**US-2: Receive Match Invitation**
> **As a** student developer
> **I want to** receive match invitations with opponent info
> **So that** my agent can prepare strategy
> **Acceptance Criteria:** Invitation includes opponent_id, game_type, timeout constraint

**US-3: Make Strategic Decision**
> **As a** student developer
> **I want to** access opponent history and standings
> **So that** my agent can make informed strategic choices
> **Acceptance Criteria:** choose_parity message includes game_history and standings

**US-4: Learn from Results**
> **As a** student developer
> **I want to** receive detailed match results
> **So that** my agent can learn and adapt strategy
> **Acceptance Criteria:** Result includes choices, random number, outcome

**US-5: Track Tournament Progress**
> **As a** student developer
> **I want to** see real-time standings updates
> **So that** I know my current ranking and performance
> **Acceptance Criteria:** Standings updated within 5 seconds of match completion

**US-6: Debug Failures**
> **As a** student developer
> **I want to** receive clear error messages with retry info
> **So that** I can quickly fix bugs in my agent
> **Acceptance Criteria:** Errors include error_code, description, retryable flag, context

---

### 5.2 Instructor Stories

**US-7: Automated Tournament Management**
> **As an** instructor
> **I want to** tournament to run automatically without manual intervention
> **So that** I can focus on teaching rather than administration
> **Acceptance Criteria:** Tournament completes all rounds automatically

**US-8: Monitor Student Performance**
> **As an** instructor
> **I want to** view detailed performance metrics for each agent
> **So that** I can assess student understanding and provide feedback
> **Acceptance Criteria:** Metrics include win rate, avg response time, error rate

**US-9: Detect Technical vs Strategic Failures**
> **As an** instructor
> **I want to** distinguish technical failures from strategic losses
> **So that** I can grade students fairly
> **Acceptance Criteria:** Logs clearly mark TECHNICAL_LOSS vs normal LOSS

---

### 5.3 System Administrator Stories

**US-10: Monitor System Health**
> **As a** system administrator
> **I want to** health check endpoints for all components
> **So that** I can detect failures proactively
> **Acceptance Criteria:** Health endpoints return status within 1 second

**US-11: Debug Production Issues**
> **As a** system administrator
> **I want to** correlated logs across all components
> **So that** I can trace issues end-to-end
> **Acceptance Criteria:** Logs queryable by conversation_id

**US-12: Scale for Large Tournaments**
> **As a** system administrator
> **I want to** add referees dynamically during tournament
> **So that** system can handle growing player counts
> **Acceptance Criteria:** New referees auto-register and receive match assignments

---

## 6. Acceptance Criteria (Consolidated)

### 6.1 Protocol Compliance
- ✅ All messages include valid envelope with required fields
- ✅ Timestamps in UTC/GMT timezone only
- ✅ Sender format follows `type:id` convention
- ✅ Auth tokens validated on all post-registration messages
- ✅ Protocol version 2.0.0 - 2.1.0 supported

### 6.2 Registration & Authentication
- ✅ Referees register successfully and receive referee_id + auth_token
- ✅ Players register successfully and receive player_id + auth_token
- ✅ Duplicate registration attempts rejected
- ✅ Late registration (after league start) rejected
- ✅ Invalid protocol versions rejected with E018 error

### 6.3 Scheduling & Game Flow
- ✅ Round-robin schedule generated correctly (all players play all others)
- ✅ Round announcements sent before round start
- ✅ Game invitations sent to correct players
- ✅ Invitation acknowledgments required within 5 seconds
- ✅ Moves collected within 30 seconds
- ✅ Invalid moves rejected with validation error

### 6.4 Timeout & Error Handling
- ✅ All message types enforce defined timeout limits
- ✅ Timeout errors trigger retry logic (max 3 attempts)
- ✅ Technical losses assigned after retry exhaustion
- ✅ Error messages include error_code, description, retryable flag
- ✅ Non-retryable errors fail immediately

### 6.5 Results & Standings
- ✅ Match results reported to League Manager within 10 seconds
- ✅ Standings updated within 5 seconds of result receipt
- ✅ Standings broadcast to all players
- ✅ Scoring correct: Win=3, Tie=1, Loss=0
- ✅ Tiebreaker logic applied correctly

### 6.6 Reliability & Recovery
- ✅ Agents can be suspended and recover
- ✅ State transitions follow defined state machine
- ✅ Conversation IDs enable end-to-end tracing
- ✅ All events logged with structured format
- ✅ System handles referee failures gracefully

---

## 7. Success Metrics

### 7.1 Functional Metrics
- **Protocol Compliance Rate**: 100% of messages conform to protocol
- **Registration Success Rate**: > 99% (failures only due to version mismatch)
- **Match Completion Rate**: > 95% (accounting for technical losses)
- **Timeout Compliance**: > 98% of responses within timeout limits
- **Error Recovery Rate**: > 80% of retryable errors succeed on retry

### 7.2 Performance Metrics
- **Registration Response Time**: < 2 seconds (avg)
- **Match Scheduling Time**: < 5 seconds for 50 players
- **Standings Update Latency**: < 5 seconds
- **Message Round-Trip Time**: < 500ms (same network)
- **Concurrent Games Supported**: ≥ 10 simultaneous matches

### 7.3 Reliability Metrics
- **System Uptime**: > 99.5% during tournament
- **Referee Availability**: ≥ 2 active referees at all times
- **Data Loss Rate**: 0% (all match results persisted)
- **Suspension Recovery Rate**: > 70% of suspended agents recover

### 7.4 User Experience Metrics
- **Student Satisfaction**: > 80% report clear protocol documentation
- **Debugging Ease**: < 30 minutes avg time to diagnose failures (via logs)
- **Tournament Duration**: Complete 20-player round-robin in < 2 hours

---

## 8. Technical Constraints

### 8.1 Port Allocation
- **League Manager**: Port 8000 (fixed)
- **Referees**: Ports 8001-8010 (up to 10 concurrent referees)
- **Players**: Ports 8101-8150 (up to 50 players)

### 8.2 Timeout Limits (Hard Constraints)
- REFEREE_REGISTER: 10 seconds
- LEAGUE_REGISTER: 10 seconds
- GAME_JOIN_ACK: 5 seconds
- CHOOSE_PARITY: 30 seconds
- GAME_OVER: 5 seconds
- MATCH_RESULT_REPORT: 10 seconds
- Default: 10 seconds

### 8.3 Retry Policy (Fixed)
- Max retries: 3
- Delay between retries: 2 seconds
- Retryable errors: E001 (timeout), E009 (connection)

### 8.4 Protocol Version
- Current: 2.1.0
- Minimum supported: 2.0.0
- Format: Semantic versioning (MAJOR.MINOR.PATCH)

### 8.5 Timezone Requirement
- **Mandatory**: All timestamps in UTC/GMT
- **Accepted formats**:
  - `20250115T10:30:00Z`
  - `20250115T10:30:00+00:00`
- **Rejected formats**:
  - Local timezones (e.g., `+02:00`)
  - No timezone indicator

### 8.6 Security Requirements
- Auth tokens: Cryptographically secure, 64+ characters
- Token format: `tok_{type}_{id}_{random}`
- Token validation: Every post-registration message
- Token storage: Environment variables (not hardcoded)

---

## 9. Dependencies

### 9.1 Internal Dependencies
- **Player Agent** depends on **League Manager** (registration)
- **Referee** depends on **League Manager** (registration, result reporting)
- **Referee** depends on **Player Agents** (game execution)
- **Standings** depends on **Match Results** (calculation)

### 9.2 External Dependencies
- MCP Server infrastructure (FastAPI, uvicorn)
- JSON-RPC 2.0 libraries
- Cryptographically secure random number generation
- Structured logging framework (loguru, structlog)
- Time synchronization (NTP for accurate UTC timestamps)

### 9.3 Development Dependencies
- Python 3.11+
- pytest for testing
- Mock frameworks for unit tests
- Load testing tools (locust, k6)

---

## 10. Timeline & Milestones

### Phase 1: Foundation (Week 1-2)
**Goal:** Core protocol infrastructure functional
- ✅ League Manager: Registration endpoints
- ✅ Referee: Registration and basic game flow
- ✅ Player: Registration and invitation handling
- ✅ Message envelope validation
- ✅ UTC timestamp enforcement
- ✅ Auth token generation and validation

**Success Criteria:**
- All three layers can register successfully
- Messages conform to protocol envelope
- Auth tokens validated correctly

---

### Phase 2: Game Execution (Week 3-4)
**Goal:** Complete game flow with error handling
- ✅ Round-robin schedule generation
- ✅ Game invitation and acknowledgment
- ✅ Move collection with timeout
- ✅ Winner determination (even/odd game)
- ✅ Result reporting and standings update
- ✅ Retry logic for transient failures

**Success Criteria:**
- Complete end-to-end match execution
- Timeout handling works correctly
- Standings update after each match
- Technical losses assigned appropriately

---

### Phase 3: Reliability & Monitoring (Week 5-6)
**Goal:** Production-ready system with monitoring
- ✅ Comprehensive error handling (all error codes)
- ✅ Agent state machine implementation
- ✅ Suspension and recovery logic
- ✅ Conversation ID tracking
- ✅ Structured logging across all components
- ✅ Health check endpoints

**Success Criteria:**
- System handles all error scenarios gracefully
- Logs enable end-to-end debugging
- Suspended agents can recover
- System runs full tournament without crashes

---

### Phase 4: Testing & Validation (Week 7)
**Goal:** Comprehensive testing and bug fixes
- ✅ Unit tests for all components
- ✅ Integration tests for full game flow
- ✅ Load testing (50 players, 10 concurrent games)
- ✅ Security testing (token validation, injection attacks)
- ✅ Protocol compliance testing

**Success Criteria:**
- Test coverage > 80%
- System handles 50 players smoothly
- No security vulnerabilities found
- All protocol messages validated

---

### Phase 5: Production Deployment (Week 8)
**Goal:** Live tournament execution
- ✅ Production deployment
- ✅ Student agent onboarding
- ✅ Live tournament execution
- ✅ Real-time monitoring
- ✅ Post-tournament analysis

**Success Criteria:**
- Tournament completes successfully
- > 95% match completion rate
- < 5 critical bugs during tournament
- Student satisfaction > 80%

---

## 11. Risk Assessment

### 11.1 High-Priority Risks

**Risk 1: Timeout Enforcement Inconsistency**
- **Probability:** Medium
- **Impact:** High (unfair matches)
- **Mitigation:**
  - Centralized timeout utility
  - Comprehensive timeout testing
  - Referee-side enforcement (single source of truth)

**Risk 2: Auth Token Security Breach**
- **Probability:** Low
- **Impact:** Critical (agent impersonation)
- **Mitigation:**
  - Cryptographically secure token generation
  - Token validation on every message
  - Token rotation (future enhancement)
  - Security audit before production

**Risk 3: Scalability Bottleneck (League Manager)**
- **Probability:** Medium
- **Impact:** High (tournament delays)
- **Mitigation:**
  - Async I/O for all operations
  - Database indexing on player_id, match_id
  - Load testing with 100+ players
  - Horizontal scaling plan (future)

---

### 11.2 Medium-Priority Risks

**Risk 4: Network Partition During Match**
- **Probability:** Medium
- **Impact:** Medium (match aborted)
- **Mitigation:**
  - Retry logic with exponential backoff
  - Connection health checks before match start
  - Match recovery protocol (future)

**Risk 5: Timestamp Synchronization Issues**
- **Probability:** Low
- **Impact:** Medium (audit trail confusion)
- **Mitigation:**
  - Mandatory NTP synchronization
  - Timestamp validation on message receipt
  - Clock skew detection and warnings

**Risk 6: Student Agent Bugs Cause Referee Crashes**
- **Probability:** High
- **Impact:** Medium (match disruption)
- **Mitigation:**
  - Comprehensive input validation
  - Sandboxed message processing
  - Circuit breaker pattern for problematic agents
  - Automatic suspension after repeated errors

---

### 11.3 Low-Priority Risks

**Risk 7: Protocol Version Fragmentation**
- **Probability:** Low
- **Impact:** Low (minor compatibility issues)
- **Mitigation:**
  - Clear versioning policy
  - Backwards compatibility within minor versions
  - Version compatibility matrix documented

---

## 12. Open Questions & Future Enhancements

### 12.1 Open Questions
1. **Q:** Should we support mid-tournament player registration?
   **A:** No for v2.1 (reject with E019), consider for v2.2

2. **Q:** How to handle referee failures mid-match?
   **A:** Match aborted, rescheduled with different referee (future)

3. **Q:** Should standings include ELO rating?
   **A:** No for v2.1, consider for v2.2 (advanced metrics)

4. **Q:** Maximum tournament size before performance degrades?
   **A:** Target: 50 players, test up to 100

### 12.2 Future Enhancements (v2.2+)
- Web-based tournament dashboard with real-time updates
- WebSocket support for live match streaming
- Multi-game support (tic-tac-toe, rock-paper-scissors)
- ELO rating system for more nuanced rankings
- Match replay and visualization
- Agent performance analytics (response time heatmaps)
- Cross-league tournaments
- Tournament brackets (single/double elimination)

---

## 13. Appendix

### 13.1 Glossary
- **MCP**: Model Context Protocol - communication protocol for AI agents
- **JSON-RPC 2.0**: Remote procedure call protocol using JSON
- **Round-Robin**: Tournament format where every player plays every other player
- **Technical Loss**: Loss due to timeout or protocol violation (not strategic failure)
- **Envelope**: Message wrapper with metadata (protocol, sender, timestamp, etc.)
- **Conversation ID**: Unique identifier for multi-message interaction (e.g., one match)
- **Auth Token**: Cryptographic token for agent authentication

### 13.2 References
- Model Context Protocol Specification: https://spec.modelcontextprotocol.io/
- JSON-RPC 2.0 Specification: https://www.jsonrpc.org/specification
- ISO 8601 Timestamp Format: https://en.wikipedia.org/wiki/ISO_8601
- Semantic Versioning: https://semver.org/

### 13.3 Document Change Log
- **v1.0 (2025-12-20)**: Initial PRD based on General League Protocol requirements

---

**Document Status:** DRAFT - Pending Review
**Next Review Date:** 2025-12-27
**Approvers:** Course Instructor, Technical Lead, Student Representatives
