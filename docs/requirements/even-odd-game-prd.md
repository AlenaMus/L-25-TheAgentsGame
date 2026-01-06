# Product Requirements Document (PRD)
# Even/Odd Game - Rules, Mechanics & Implementation

**Document Version:** 1.0
**Date:** 2025-12-20
**Status:** Draft
**Product Owner:** AI Development Course Team
**Target Release:** Phase 1 - Foundation
**Related Documents:**
- `league-system-prd.md` (League Management System)
- `game-protocol-messages-prd.md` (Protocol Messages)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Game Overview](#game-overview)
3. [Game Rules & Mechanics](#game-rules--mechanics)
4. [Game Flow & Phases](#game-flow--phases)
5. [Game State Management](#game-state-management)
6. [Scoring System](#scoring-system)
7. [Round-Robin Tournament Structure](#round-robin-tournament-structure)
8. [Player Strategies](#player-strategies)
9. [Game Rules Module Architecture](#game-rules-module-architecture)
10. [Extensibility to Other Games](#extensibility-to-other-games)
11. [User Stories](#user-stories)
12. [Acceptance Criteria](#acceptance-criteria)
13. [Success Metrics](#success-metrics)
14. [Technical Constraints](#technical-constraints)
15. [Risk Assessment](#risk-assessment)

---

## 1. Executive Summary

### 1.1 Problem Statement
The league system needs a simple, deterministic game that can demonstrate the protocol's capabilities while being easy for students to understand and implement strategies for. The game must be fair, quick to play, and suitable for testing agent decision-making under uncertainty.

### 1.2 Solution Overview
**Even/Odd** is a simultaneous-choice game where two players independently choose "even" or "odd", then a random number (1-10) is drawn to determine the winner. The game demonstrates protocol concepts while being simple enough for students to focus on strategy implementation rather than complex game mechanics.

### 1.3 Key Benefits
- **Simple Rules**: Explained in 30 seconds, implemented in 30 minutes
- **Fair**: Pure chance baseline (50/50) - no inherent advantage
- **Fast**: Single round completes in < 5 seconds
- **Deterministic Outcome**: Clear winner determination logic
- **Strategy-Rich**: Despite simplicity, allows for pattern detection and adaptation
- **Protocol Demonstration**: Perfect vehicle for teaching distributed systems

---

## 2. Game Overview

### 2.1 Game Classification
- **Type:** Simultaneous-move game (both players choose at the same time)
- **Category:** Game of chance with strategic elements
- **Players:** Exactly 2 players per match
- **Duration:** Single-round (one choice per player)
- **Skill vs Luck:** 0% skill vs 100% luck (with random opponent)
- **Complexity:** Low (suitable for beginners)

### 2.2 Historical Context
Even/Odd (also known as "Odds and Evens" or "Morra") is an ancient game dating back to ancient Rome. In its traditional form, players show fingers simultaneously. This digital version simplifies to pure choice + random draw.

### 2.3 Educational Value
**For Students:**
- Learn multi-agent communication protocols
- Practice handling uncertainty and randomness
- Explore pattern detection and statistical analysis
- Understand timeout constraints and failure handling
- Experience tournament dynamics and meta-strategy

**For Instructors:**
- Easy to explain and grade
- Clear distinction between technical and strategic failures
- Scalable to large class sizes
- Extensible to more complex games later

---

## 3. Game Rules & Mechanics

### 3.1 Core Game Rules

#### 3.1.1 Setup
- **Players:** Exactly 2 players (Player A and Player B)
- **Choices:** Each player chooses either "even" or "odd"
- **Simultaneity:** Choices made without knowing opponent's choice
- **Random Element:** Referee draws random integer between 1 and 10 (inclusive)

#### 3.1.2 Winning Conditions
1. **Number is Even (2, 4, 6, 8, 10):**
   - Player who chose "even" **wins**
   - Player who chose "odd" **loses**

2. **Number is Odd (1, 3, 5, 7, 9):**
   - Player who chose "odd" **wins**
   - Player who chose "even" **loses**

3. **Both Players Chose Same (Both "even" or both "odd"):**
   - If number matches their choice → both "win" → **Draw (tie)**
   - If number doesn't match → both "lose" → **Draw (tie)**

#### 3.1.3 Game Examples

**Table 1: Even/Odd Game Outcome Examples**

| Match | Player A Choice | Player B Choice | Random Number | Number Parity | Winner | Explanation |
|-------|----------------|----------------|---------------|---------------|--------|-------------|
| 1 | even | odd | 8 | even | Player A | A chose even, number is even |
| 2 | even | odd | 7 | odd | Player B | B chose odd, number is odd |
| 3 | odd | odd | 4 | even | Draw | Both chose odd, number is even (both wrong) |
| 4 | even | even | 6 | even | Draw | Both chose even, number is even (both correct) |
| 5 | even | odd | 10 | even | Player A | A chose even, number is even |
| 6 | odd | even | 1 | odd | Player A | A chose odd, number is odd |

**Key Insight:** When players choose differently, there's always exactly one winner (50/50 probability). When players choose the same, it's always a draw (regardless of number).

---

### 3.2 Randomness Requirements

#### 3.2.1 Random Number Generation
**Critical Requirement:** The referee MUST use cryptographically secure random number generation.

**Why Cryptographic Randomness Matters:**
- **Predictability:** Pseudo-random generators (like simple LCG) can be predicted by analyzing patterns
- **Fairness:** Weak randomness could give advantage to agents that detect patterns
- **Security:** Prevents agents from gaming the system through seed prediction

**Implementation Requirements:**
- **Python:** Use `secrets.randbelow(10) + 1` (NOT `random.randint()`)
- **JavaScript:** Use `crypto.getRandomValues()` (NOT `Math.random()`)
- **Uniform Distribution:** Each number 1-10 must have exactly 10% probability
- **Independence:** Each draw must be independent (no correlation between draws)

#### 3.2.2 Statistical Validation
**Acceptance Criteria for Randomness:**
- Run 10,000 draws → each number appears 900-1100 times (90% confidence interval)
- Chi-squared test: p-value > 0.05 (null hypothesis: uniform distribution)
- No autocorrelation between consecutive draws (correlation coefficient < 0.05)

**Validation Code Example (Python):**
```python
import secrets
from collections import Counter

# Generate 10,000 random numbers
draws = [secrets.randbelow(10) + 1 for _ in range(10000)]

# Count occurrences
counts = Counter(draws)

# Validate distribution
for num in range(1, 11):
    count = counts[num]
    assert 900 <= count <= 1100, f"Number {num} appeared {count} times (expected 900-1100)"

# Validate even/odd distribution
even_count = sum(1 for d in draws if d % 2 == 0)
odd_count = sum(1 for d in draws if d % 2 == 1)
assert 4900 <= even_count <= 5100, f"Even count: {even_count} (expected ~5000)"
assert 4900 <= odd_count <= 5100, f"Odd count: {odd_count} (expected ~5000)"
```

---

### 3.3 Choice Validation

#### 3.3.1 Valid Choices
**Allowed Values:** Exactly `"even"` or `"odd"` (lowercase, string type)

**Validation Rules:**
- ✅ `"even"` → Valid
- ✅ `"odd"` → Valid
- ❌ `"Even"` → Invalid (case-sensitive)
- ❌ `"EVEN"` → Invalid (must be lowercase)
- ❌ `"e"` → Invalid (must be full word)
- ❌ `0` → Invalid (must be string, not integer)
- ❌ `true` → Invalid (must be string, not boolean)
- ❌ `"maybe"` → Invalid (not a valid choice)
- ❌ `null` → Invalid (must be present)
- ❌ `""` → Invalid (empty string)

#### 3.3.2 Validation Error Handling
**If player sends invalid choice:**
1. Referee sends `GAME_ERROR` with error code `E004` (INVALID_PARITY_CHOICE)
2. Player has opportunity to retry (within remaining timeout window)
3. If retry succeeds → game continues normally
4. If timeout expires before valid choice → `TECHNICAL_LOSS` for that player

---

## 4. Game Flow & Phases

### 4.1 Complete Game Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│ PHASE 1: Game Invitation                                     │
│ Referee → Player A: GAME_INVITATION                          │
│ Referee → Player B: GAME_INVITATION                          │
│ Timeout: 5 seconds per player                                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 2: Arrival Confirmation                                │
│ Player A → Referee: GAME_JOIN_ACK                            │
│ Player B → Referee: GAME_JOIN_ACK                            │
│ If rejected or timeout → TECHNICAL_LOSS                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 3: Collecting Choices                                  │
│ Referee → Player A: CHOOSE_PARITY_CALL                       │
│ Referee → Player B: CHOOSE_PARITY_CALL                       │
│ (Sent simultaneously - players don't see each other's choice)│
│ Player A → Referee: CHOOSE_PARITY_RESPONSE ("even" or "odd") │
│ Player B → Referee: CHOOSE_PARITY_RESPONSE ("even" or "odd") │
│ Timeout: 30 seconds per player                               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 4: Drawing Number                                      │
│ Referee: number = secrets.randbelow(10) + 1                  │
│ Duration: < 100ms                                            │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 5: Determining Winner                                  │
│ Referee: Apply winning conditions                            │
│ - If number is even → player who chose "even" wins           │
│ - If number is odd → player who chose "odd" wins             │
│ - If both chose same → draw                                  │
│ Duration: < 10ms                                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ PHASE 6: Reporting Result                                    │
│ Referee → Player A: GAME_OVER                                │
│ Referee → Player B: GAME_OVER                                │
│ Referee → League Manager: MATCH_RESULT_REPORT                │
│ Timeout: 5 seconds (acknowledgment)                          │
└─────────────────────────────────────────────────────────────┘
                            ↓
                         FINISHED
```

---

### 4.2 Phase Details

#### 4.2.1 Phase 1: Game Invitation
**Duration:** 5 seconds timeout per player
**Participants:** Referee → Players

**Purpose:** Notify players that a match is starting and confirm their availability.

**Message Sent:** `GAME_INVITATION`
**Expected Response:** `GAME_JOIN_ACK`

**Key Information Provided:**
- `match_id`: Unique game identifier
- `round_id`: Tournament round number
- `game_type`: "even_odd"
- `opponent_id`: Who the player is playing against
- `role_in_match`: "PLAYER_A" or "PLAYER_B" (for logging/tracking)

**Failure Scenarios:**
- Player doesn't respond within 5 seconds → TECHNICAL_LOSS (forfeit)
- Player responds with `accept: false` → TECHNICAL_LOSS (forfeit)
- Connection error → Retry (up to 3 attempts), then TECHNICAL_LOSS

**User Story:**
> **As a** player agent
> **I want to** receive match invitations with opponent information
> **So that** I can prepare my strategy and confirm readiness

---

#### 4.2.2 Phase 2: Arrival Confirmation
**Duration:** Included in Phase 1 timeout (5 seconds)
**Participants:** Players → Referee

**Purpose:** Players explicitly acknowledge they're ready to play.

**Message Sent:** `GAME_JOIN_ACK`
**Fields:**
- `accept`: `true` (ready to play) or `false` (reject invitation)
- `arrival_timestamp`: Player's local timestamp (for latency debugging)

**Transition Condition:** Both players send `accept: true` → proceed to Phase 3

**Failure Scenarios:**
- One player rejects → other player gets automatic win (3 points)
- One player times out → other player gets automatic win
- Both players timeout/reject → both get 0 points (double forfeit)

**Design Rationale:**
- Explicit confirmation prevents players from being "surprised" by matches
- Timestamp allows debugging network latency issues
- Accept/reject mechanism allows agents to gracefully decline if in error state

---

#### 4.2.3 Phase 3: Collecting Choices
**Duration:** 30 seconds timeout per player
**Participants:** Referee ↔ Players

**Purpose:** Collect strategic choices from both players without revealing them to each other.

**Critical Requirement:** Choices must be collected **simultaneously** (not sequentially).
- ❌ **Wrong:** Ask Player A, wait for response, then ask Player B
- ✅ **Correct:** Ask both players at the same time, wait for both responses

**Why Simultaneity Matters:**
- **Fairness:** Sequential collection gives second player timing information
- **Strategic Integrity:** Players can't react to opponent's choice
- **Protocol Principle:** Simulates "simultaneous reveal" in physical games

**Message Sent:** `CHOOSE_PARITY_CALL`
**Expected Response:** `CHOOSE_PARITY_RESPONSE`

**Context Provided to Players:**
- `opponent_id`: Who they're playing against
- `round_id`: Current tournament round
- `your_standings`: Player's current win/loss/draw record (optional)
- `deadline`: UTC timestamp when choice must be received

**Validation:**
- Choice must be exactly `"even"` or `"odd"` (lowercase string)
- Invalid choice → `GAME_ERROR` E004, allow retry
- Timeout → retry up to 3 times (2-second delay), then TECHNICAL_LOSS

**User Story:**
> **As a** player agent
> **I want to** make my choice without knowing my opponent's choice
> **So that** the game is fair and tests my strategy, not my reaction time

---

#### 4.2.4 Phase 4: Drawing Number
**Duration:** < 100ms
**Participants:** Referee (internal)

**Purpose:** Generate cryptographically secure random number to determine outcome.

**Algorithm:**
```python
import secrets

def draw_number() -> int:
    """
    Draw a cryptographically secure random integer between 1 and 10 (inclusive).

    Returns:
        int: Random number in range [1, 10]
    """
    return secrets.randbelow(10) + 1
```

**Logging Requirements:**
- Log the drawn number with timestamp
- Log the random source used (for audit)
- Include in match result for transparency

**Acceptance Criteria:**
- ✅ Number is between 1 and 10 (inclusive)
- ✅ Generation uses cryptographically secure source
- ✅ Generation completes in < 100ms
- ✅ Number logged before result determination

---

#### 4.2.5 Phase 5: Determining Winner
**Duration:** < 10ms
**Participants:** Referee (internal)

**Purpose:** Apply game rules to determine match outcome.

**Winner Determination Algorithm:**
```python
def determine_winner(choice_a: str, choice_b: str, number: int) -> dict:
    """
    Determine winner based on choices and drawn number.

    Args:
        choice_a: Player A's choice ("even" or "odd")
        choice_b: Player B's choice ("even" or "odd")
        number: Drawn number (1-10)

    Returns:
        dict with keys: winner, result_type, reason
    """
    number_parity = "even" if number % 2 == 0 else "odd"

    # Case 1: Both chose the same
    if choice_a == choice_b:
        return {
            "winner": None,
            "result_type": "DRAW",
            "reason": f"Both chose {choice_a}, number was {number} ({number_parity})"
        }

    # Case 2: Different choices - determine winner
    if choice_a == number_parity:
        return {
            "winner": "player_a",
            "result_type": "WIN",
            "reason": f"Player A chose {choice_a}, number was {number} ({number_parity})"
        }
    else:
        return {
            "winner": "player_b",
            "result_type": "WIN",
            "reason": f"Player B chose {choice_b}, number was {number} ({number_parity})"
        }
```

**Edge Cases:**
- Technical loss for one player → other player wins by default
- Technical loss for both players → both get 0 points
- Invalid choice after max retries → treated as technical loss

---

#### 4.2.6 Phase 6: Reporting Result
**Duration:** 5 seconds timeout (for player acknowledgment)
**Participants:** Referee → Players, Referee → League Manager

**Purpose:** Notify all parties of match outcome and update standings.

**Messages Sent:**
1. `GAME_OVER` → Both players (identical message)
2. `MATCH_RESULT_REPORT` → League Manager

**Information Included in GAME_OVER:**
- `winner_player_id`: Who won (or null for draw)
- `result_type`: "WIN", "DRAW", or "TECHNICAL_LOSS"
- `drawn_number`: The random number that was drawn
- `number_parity`: "even" or "odd"
- `choices`: Map of player_id → choice (transparent reveal)
- `points_awarded`: Map of player_id → points (3, 1, or 0)
- `reason`: Human-readable explanation

**Player Responsibilities:**
- Store result in game history (for strategy learning)
- Update internal opponent profile (for pattern detection)
- Optionally acknowledge receipt (not enforced)

**League Manager Responsibilities:**
- Update standings immediately
- Broadcast `LEAGUE_STANDINGS_UPDATE` to all players
- Persist result for audit trail

**User Story:**
> **As a** player agent
> **I want to** see the complete match outcome (choices, number, result)
> **So that** I can learn from the game and update my strategy

---

## 5. Game State Management

### 5.1 Game State Machine

#### 5.1.1 States

**State Diagram:**
```
          [START]
             ↓
    ┌──────────────────┐
    │ WAITING_FOR_     │ ← Initial state after match creation
    │ PLAYERS          │
    └──────────────────┘
             ↓ (both players confirm arrival)
    ┌──────────────────┐
    │ COLLECTING_      │ ← Waiting for player choices
    │ CHOICES          │
    └──────────────────┘
             ↓ (both choices received)
    ┌──────────────────┐
    │ DRAWING_NUMBER   │ ← Generating random number
    └──────────────────┘
             ↓ (number drawn)
    ┌──────────────────┐
    │ EVALUATING       │ ← Determining winner
    └──────────────────┘
             ↓ (winner determined)
    ┌──────────────────┐
    │ FINISHED         │ ← Terminal state
    └──────────────────┘

    From any state:
             ↓ (critical error or double timeout)
    ┌──────────────────┐
    │ ABORTED          │ ← Terminal state (error)
    └──────────────────┘
```

---

#### 5.1.2 State Definitions

**WAITING_FOR_PLAYERS**
- **Entry Condition:** Match created by League Manager, assigned to referee
- **Active Actions:**
  - Referee sends GAME_INVITATION to both players
  - Waiting for GAME_JOIN_ACK from both players
  - Timeout monitoring (5 seconds per player)
- **Exit Condition:** Both players send `accept: true`
- **Alternative Exit:** Timeout or reject → ABORTED (winner assigned to non-failing player)
- **Data Stored:**
  - Player IDs
  - Invitation timestamps
  - Acknowledgment timestamps

**COLLECTING_CHOICES**
- **Entry Condition:** Both players confirmed arrival
- **Active Actions:**
  - Referee sends CHOOSE_PARITY_CALL to both players simultaneously
  - Waiting for CHOOSE_PARITY_RESPONSE from both players
  - Validate choices (must be "even" or "odd")
  - Timeout monitoring (30 seconds per player)
  - Retry logic for timeouts/errors
- **Exit Condition:** Both valid choices received
- **Alternative Exit:** Max retries exhausted → ABORTED (TECHNICAL_LOSS)
- **Data Stored:**
  - Player choices
  - Response timestamps
  - Retry attempts count

**DRAWING_NUMBER**
- **Entry Condition:** Both choices received and validated
- **Active Actions:**
  - Generate cryptographically secure random number (1-10)
  - Log drawn number with timestamp
- **Exit Condition:** Number successfully generated (deterministic, always succeeds)
- **Duration:** < 100ms
- **Data Stored:**
  - Drawn number
  - Number parity ("even" or "odd")
  - Random generation timestamp

**EVALUATING**
- **Entry Condition:** Number drawn
- **Active Actions:**
  - Apply winner determination algorithm
  - Calculate points awarded (3-1-0)
  - Generate human-readable result reason
- **Exit Condition:** Winner determined (deterministic, always succeeds)
- **Duration:** < 10ms
- **Data Stored:**
  - Winner player_id (or null for draw)
  - Result type (WIN/DRAW/TECHNICAL_LOSS)
  - Points awarded to each player
  - Reason string

**FINISHED**
- **Entry Condition:** Winner determined
- **Active Actions:**
  - Send GAME_OVER to both players
  - Send MATCH_RESULT_REPORT to League Manager
  - Wait for player acknowledgments (optional, best-effort)
  - Cleanup resources
- **Exit Condition:** Terminal state (never exits)
- **Data Stored:**
  - Complete match record
  - All messages sent/received
  - Timestamps for audit

**ABORTED**
- **Entry Condition:** Critical error or timeout from any state
- **Active Actions:**
  - Determine if partial result possible (e.g., one player failed → other wins)
  - Send GAME_ERROR to affected players
  - Send MATCH_RESULT_REPORT to League Manager (with TECHNICAL_LOSS)
  - Log error details for debugging
- **Exit Condition:** Terminal state (never exits)
- **Data Stored:**
  - Error details
  - Partial game state
  - Failure reason

---

#### 5.1.3 State Transition Rules

**Valid Transitions:**
- WAITING_FOR_PLAYERS → COLLECTING_CHOICES (both players confirmed)
- WAITING_FOR_PLAYERS → ABORTED (timeout or reject)
- COLLECTING_CHOICES → DRAWING_NUMBER (both choices received)
- COLLECTING_CHOICES → ABORTED (max retries exhausted)
- DRAWING_NUMBER → EVALUATING (always, deterministic)
- EVALUATING → FINISHED (always, deterministic)

**Invalid Transitions (must be prevented):**
- FINISHED → any state (terminal)
- ABORTED → any state (terminal)
- COLLECTING_CHOICES → WAITING_FOR_PLAYERS (cannot go backwards)
- Any state → DRAWING_NUMBER (except from COLLECTING_CHOICES)

---

### 5.2 State Persistence

#### 5.2.1 Why Persist State?
- **Recovery:** Referee crashes can be recovered by reloading state
- **Audit:** Complete game history for dispute resolution
- **Debugging:** Replay games to identify bugs
- **Analytics:** Analyze game patterns and player behavior

#### 5.2.2 What to Persist
**Minimum Required:**
- Current state
- Match ID, round ID, league ID
- Player IDs and choices (once received)
- Drawn number (once generated)
- Winner and points (once determined)
- All timestamps

**Recommended Additional:**
- All messages sent/received (full protocol trace)
- Retry attempts and errors
- Timeout warnings
- State transition history

#### 5.2.3 Persistence Implementation
**Storage Options:**
1. **JSON File** (simplest, suitable for small tournaments)
   - File per match: `match_{match_id}_state.json`
   - Updated after each state transition
   - Easy to inspect manually

2. **SQLite Database** (recommended for production)
   - Tables: matches, game_states, messages, state_transitions
   - ACID guarantees
   - Queryable for analytics

3. **Redis** (for distributed deployments)
   - In-memory for speed
   - Persistence to disk for durability
   - Pub/sub for real-time updates

**Example State JSON:**
```json
{
  "match_id": "R1M1",
  "current_state": "COLLECTING_CHOICES",
  "created_at": "20250115T10:30:00Z",
  "updated_at": "20250115T10:30:15Z",
  "players": {
    "player_a": {
      "player_id": "P01",
      "confirmed_arrival": true,
      "choice": null,
      "choice_timestamp": null
    },
    "player_b": {
      "player_id": "P02",
      "confirmed_arrival": true,
      "choice": "even",
      "choice_timestamp": "20250115T10:30:12Z"
    }
  },
  "drawn_number": null,
  "winner": null,
  "state_history": [
    {"state": "WAITING_FOR_PLAYERS", "timestamp": "20250115T10:30:00Z"},
    {"state": "COLLECTING_CHOICES", "timestamp": "20250115T10:30:08Z"}
  ]
}
```

---

## 6. Scoring System

### 6.1 Single Game Scoring

**Table 2: Points Awarded by Result**

| Result Type | Winner Points | Loser Points | Notes |
|-------------|---------------|--------------|-------|
| **WIN** | 3 | 0 | Standard victory |
| **DRAW** | 1 | 1 | Both players get equal points |
| **TECHNICAL_LOSS** | 3 (opponent) | 0 | Failure to respond/invalid move |
| **DOUBLE FORFEIT** | 0 | 0 | Both players failed (rare) |

**Design Rationale:**
- **3 points for win:** Incentivizes winning over drawing
- **1 point for draw:** Draws still contribute to standings (better than loss)
- **0 points for loss:** Clear penalty for losing
- **Technical loss = normal loss:** No distinction in points (only in statistics)

---

### 6.2 Tournament Standings Calculation

#### 6.2.1 Primary Ranking: Total Points
**Formula:** `total_points = (wins × 3) + (draws × 1) + (losses × 0)`

**Example:**
- Agent A: 5 wins, 2 draws, 1 loss → 5×3 + 2×1 + 1×0 = **17 points**
- Agent B: 4 wins, 4 draws, 0 losses → 4×3 + 4×1 + 0×0 = **16 points**
- Agent A ranks higher despite having a loss

---

#### 6.2.2 Tiebreaker Rules (in order)

**When two agents have same total points, apply tiebreakers in this order:**

1. **Head-to-Head Record**
   - If agents have played each other, winner of that match ranks higher
   - If they drew head-to-head, proceed to next tiebreaker

2. **Win Percentage**
   - Formula: `win_percentage = wins / games_played`
   - Higher percentage ranks higher
   - Example: 3/5 (60%) beats 5/10 (50%)

3. **Total Wins**
   - Absolute number of wins (not percentage)
   - Rewards consistent winning over drawing

4. **Draw Count** (lower is better)
   - Fewer draws indicates more decisive play
   - Discourages "playing for draw" strategy

5. **Alphabetical by Player ID**
   - Ultimate tiebreaker when all else equal
   - Deterministic and stable

**Example Tiebreaker Scenario:**
```
Agent P01: 12 points (3W, 3D, 0L), Win% = 50%
Agent P02: 12 points (4W, 0D, 2L), Win% = 67%

→ P02 ranks higher (better win percentage)
```

---

### 6.3 Statistical Tracking

#### 6.3.1 Required Statistics (per player)
- `games_played`: Total matches
- `wins`: Number of wins
- `losses`: Number of losses
- `draws`: Number of draws
- `points`: Total points
- `win_rate`: wins / games_played
- `draw_rate`: draws / games_played
- `loss_rate`: losses / games_played

#### 6.3.2 Optional Advanced Statistics
- `technical_losses`: Losses due to timeout/error (subset of losses)
- `avg_response_time`: Average time to respond to CHOOSE_PARITY_CALL
- `choice_distribution`: Count of "even" vs "odd" choices
- `opponent_specific_records`: Win/loss record against each opponent
- `round_by_round_performance`: Points earned per round

#### 6.3.3 Statistics Use Cases
- **Grading:** Distinguish technical failures from strategic losses
- **Debugging:** Identify performance bottlenecks (response time)
- **Strategy Analysis:** Detect patterns (always choosing "even")
- **Tournament Balancing:** Identify dominant agents for future adjustments

---

## 7. Round-Robin Tournament Structure

### 7.1 Round-Robin Basics

#### 7.1.1 Definition
**Round-Robin:** Tournament format where every player plays against every other player exactly once.

**Why Round-Robin?**
- **Fairness:** No bracket luck - everyone plays same opponents
- **Complete Data:** N×(N-1)/2 games provide rich dataset
- **Clear Winner:** Player with most points is unambiguous champion
- **No Elimination:** Losing early doesn't eliminate you (good for learning)

---

### 7.2 Tournament Math

#### 7.2.1 Number of Matches Formula
For `N` players: **Total Matches = N × (N-1) / 2**

**Examples:**
- 4 players: 4×3/2 = **6 matches**
- 10 players: 10×9/2 = **45 matches**
- 20 players: 20×19/2 = **190 matches**
- 50 players: 50×49/2 = **1,225 matches**

#### 7.2.2 Number of Rounds
- **Even N:** N - 1 rounds
- **Odd N:** N rounds (one player gets bye each round)

**Example (4 players):**
- Total matches: 6
- Rounds: 3 (4 - 1)
- Matches per round: 2

**Example (5 players with byes):**
- Total matches: 10
- Rounds: 5
- Matches per round: 2 (one player has bye)

---

### 7.3 Example Tournament Schedule

#### 7.3.1 4-Player Tournament

**Players:** P01, P02, P03, P04

**Table 3: Complete Schedule for 4 Players**

| Round | Match ID | Player A | Player B | Referee |
|-------|----------|----------|----------|---------|
| **Round 1** | R1M1 | P01 | P02 | REF01 |
| | R1M2 | P03 | P04 | REF02 |
| **Round 2** | R2M1 | P01 | P03 | REF01 |
| | R2M2 | P02 | P04 | REF02 |
| **Round 3** | R3M1 | P01 | P04 | REF01 |
| | R3M2 | P02 | P03 | REF02 |

**Verification:**
- ✅ Each player plays 3 matches (N-1 = 3)
- ✅ Total 6 matches (4×3/2 = 6)
- ✅ 3 rounds (N-1 = 3)
- ✅ Load balanced across 2 referees

---

#### 7.3.2 5-Player Tournament (with Byes)

**Players:** P01, P02, P03, P04, P05

**Table 4: Complete Schedule for 5 Players (with Byes)**

| Round | Match ID | Player A | Player B | Bye Player | Referee |
|-------|----------|----------|----------|------------|---------|
| **Round 1** | R1M1 | P01 | P02 | P05 | REF01 |
| | R1M2 | P03 | P04 | | REF02 |
| **Round 2** | R2M1 | P01 | P03 | P04 | REF01 |
| | R2M2 | P02 | P05 | | REF02 |
| **Round 3** | R3M1 | P01 | P04 | P03 | REF01 |
| | R3M2 | P02 | P03 | | REF02... wait, this isn't right

Let me recalculate:
- 5 players = 10 total matches (5×4/2)
- 5 rounds (one bye per round)
- 2 matches per round

| Round | Match ID | Player A | Player B | Bye Player | Referee |
|-------|----------|----------|----------|------------|---------|
| **Round 1** | R1M1 | P02 | P03 | P01 | REF01 |
| | R1M2 | P04 | P05 | | REF02 |
| **Round 2** | R2M1 | P01 | P03 | P02 | REF01 |
| | R2M2 | P04 | P05 | ... (continues)

**Bye Handling:**
- Player with bye automatically gets 0 points for that "match"
- Does NOT count as a loss (no penalty)
- `games_played` doesn't increment
- Bye rotates each round (fair distribution)

---

### 7.4 Scheduling Algorithm

#### 7.4.1 Round-Robin Algorithm (Even Players)
**Classic Circle Method:**

```python
def generate_round_robin_schedule(player_ids: list[str]) -> list[list[tuple]]:
    """
    Generate round-robin schedule using circle method.

    Args:
        player_ids: List of player IDs (must be even number)

    Returns:
        List of rounds, each containing list of (player_a, player_b) tuples
    """
    n = len(player_ids)
    if n % 2 == 1:
        player_ids.append("BYE")  # Add dummy player for odd case
        n += 1

    schedule = []
    for round_num in range(n - 1):
        round_matches = []
        for i in range(n // 2):
            player_a = player_ids[i]
            player_b = player_ids[n - 1 - i]
            if player_a != "BYE" and player_b != "BYE":
                round_matches.append((player_a, player_b))
        schedule.append(round_matches)

        # Rotate players (keep first player fixed)
        player_ids = [player_ids[0]] + [player_ids[-1]] + player_ids[1:-1]

    return schedule
```

**Example Output for [P01, P02, P03, P04]:**
```python
[
  [("P01", "P02"), ("P03", "P04")],  # Round 1
  [("P01", "P03"), ("P02", "P04")],  # Round 2
  [("P01", "P04"), ("P02", "P03")]   # Round 3
]
```

---

### 7.5 Tournament Timeline Estimation

#### 7.5.1 Time per Match
**Breakdown:**
- Invitation + arrival: 5 seconds
- Choice collection: 30 seconds (max timeout)
- Drawing + evaluation: 0.1 seconds
- Result reporting: 5 seconds
- **Total:** ~40 seconds worst case, ~15 seconds typical

**Assumption:** Average 20 seconds per match (players respond quickly)

#### 7.5.2 Tournament Duration Examples

**Table 5: Estimated Tournament Durations**

| Players | Total Matches | Sequential Time | Parallel Time (2 refs) | Parallel Time (10 refs) |
|---------|---------------|-----------------|------------------------|-------------------------|
| 4 | 6 | 2 min | 1 min | 1 min |
| 10 | 45 | 15 min | 8 min | 2 min |
| 20 | 190 | 63 min | 32 min | 7 min |
| 50 | 1,225 | 408 min (6.8 hrs) | 204 min (3.4 hrs) | 41 min |

**Key Insight:** Parallelization is critical for large tournaments. With 10 referees, even 50 players completes in under 1 hour.

---

## 8. Player Strategies

### 8.1 Strategy Classification

#### 8.1.1 Random Strategy (Baseline)
**Description:** Choose "even" or "odd" with 50/50 probability, independent of any history or context.

**Expected Win Rate:** 50% (against random opponent)

**Implementation:**
```python
import random

def choose_parity_random() -> str:
    """
    Random strategy: 50/50 choice between even and odd.

    Returns:
        "even" or "odd" with equal probability
    """
    return random.choice(["even", "odd"])
```

**Advantages:**
- Simple to implement (5 lines of code)
- Unexploitable (no patterns to detect)
- Guaranteed 50% win rate against any opponent long-term

**Disadvantages:**
- Cannot exploit opponent patterns
- Misses opportunities to gain advantage
- Boring (no learning or adaptation)

**When to Use:**
- Baseline for comparison
- Fallback when pattern detection fails
- Against unknown opponents initially

---

#### 8.1.2 History-Based Strategy (Pattern Detection)
**Description:** Analyze opponent's past choices to detect patterns, then exploit them.

**Expected Win Rate:** > 50% (if opponent has patterns), 50% (if opponent is random)

**Pattern Detection Approaches:**

**1. Frequency Analysis:**
```python
def analyze_opponent_frequency(game_history: list) -> dict:
    """
    Count opponent's choice frequency.

    Args:
        game_history: List of past games with this opponent

    Returns:
        {"even": count, "odd": count, "bias": "even"|"odd"|"none"}
    """
    choices = [game["opponent_choice"] for game in game_history]
    even_count = choices.count("even")
    odd_count = choices.count("odd")

    # Statistical significance test (chi-squared)
    total = len(choices)
    if total < 10:
        return {"bias": "none"}  # Not enough data

    expected = total / 2
    chi_squared = ((even_count - expected)**2 / expected +
                   (odd_count - expected)**2 / expected)

    # Chi-squared critical value for p=0.05, df=1 is 3.841
    if chi_squared > 3.841:
        bias = "even" if even_count > odd_count else "odd"
        return {"even": even_count, "odd": odd_count, "bias": bias}
    else:
        return {"bias": "none"}  # No significant pattern
```

**2. Streak Detection:**
```python
def detect_alternating_pattern(game_history: list) -> bool:
    """
    Detect if opponent alternates choices (even, odd, even, odd, ...)

    Returns:
        True if opponent alternates consistently, False otherwise
    """
    if len(game_history) < 4:
        return False

    choices = [game["opponent_choice"] for game in game_history[-10:]]
    alternations = 0
    for i in range(1, len(choices)):
        if choices[i] != choices[i-1]:
            alternations += 1

    # If 80%+ are alternations, pattern detected
    return (alternations / (len(choices) - 1)) > 0.8
```

**3. Conditional Probability:**
```python
def predict_next_choice(game_history: list) -> str:
    """
    Predict opponent's next choice based on what they did after wins/losses.

    Example: If opponent always chooses "even" after losing, exploit this.
    """
    if len(game_history) < 3:
        return "even"  # Default to even if not enough data

    last_game = game_history[-1]

    # Find all games where opponent had same result as last game
    similar_games = [
        game for game in game_history[:-1]
        if game["result"] == last_game["result"]
    ]

    if not similar_games:
        return "even"

    # What did opponent choose AFTER games with similar result?
    next_choices = []
    for i, game in enumerate(game_history[:-1]):
        if game["result"] == last_game["result"]:
            next_choices.append(game_history[i+1]["opponent_choice"])

    # Return most common choice
    return max(set(next_choices), key=next_choices.count)
```

**Strategy Logic:**
```python
def choose_parity_adaptive(opponent_id: str, game_history: list) -> str:
    """
    Adaptive strategy that detects and exploits patterns.

    Args:
        opponent_id: ID of opponent
        game_history: Past games against this opponent

    Returns:
        "even" or "odd" based on pattern detection
    """
    # Get opponent-specific history
    opp_history = [g for g in game_history if g["opponent_id"] == opponent_id]

    # Not enough data - play random
    if len(opp_history) < 5:
        return random.choice(["even", "odd"])

    # Check for frequency bias
    freq_analysis = analyze_opponent_frequency(opp_history)
    if freq_analysis["bias"] != "none":
        # Opponent biased toward "even" → choose "even" to win when number is even
        return freq_analysis["bias"]

    # Check for alternating pattern
    if detect_alternating_pattern(opp_history):
        last_choice = opp_history[-1]["opponent_choice"]
        predicted_choice = "odd" if last_choice == "even" else "even"
        return predicted_choice  # Match their predicted choice

    # Check conditional probability
    predicted = predict_next_choice(opp_history)
    return predicted
```

**Advantages:**
- Exploits non-random opponents
- Can achieve > 60% win rate against patterned players
- Educational value (teaches statistical analysis)

**Disadvantages:**
- Doesn't improve against random opponents
- Risk of overfitting to noise
- Requires sufficient game history

**Note:** Since the random number draw is truly random, pattern detection on the DRAWS is useless. The value is in detecting patterns in OPPONENT CHOICES.

---

#### 8.1.3 LLM-Driven Strategy (Optional Advanced)
**Description:** Use a language model (Claude, GPT-4) to analyze game context and make strategic decisions.

**Expected Win Rate:** ~50% (LLMs don't improve on pure randomness, but can provide interesting reasoning)

**Implementation Example:**
```python
import anthropic

def choose_parity_llm(opponent_id: str, game_history: list, standings: list) -> str:
    """
    Use Claude API to make strategic decision.

    Args:
        opponent_id: Current opponent
        game_history: Past game results
        standings: Current tournament standings

    Returns:
        "even" or "odd" based on LLM reasoning
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    # Build context prompt
    prompt = f"""
You are playing an Even/Odd game in a tournament.

GAME RULES:
- You and opponent each choose "even" or "odd" simultaneously
- Referee draws random number 1-10
- If number is even, player who chose "even" wins
- If number is odd, player who chose "odd" wins

CURRENT SITUATION:
- Your opponent: {opponent_id}
- Your current rank: {get_my_rank(standings)}
- Opponent's current rank: {get_opponent_rank(opponent_id, standings)}

GAME HISTORY vs {opponent_id}:
{format_game_history(game_history, opponent_id)}

ANALYSIS:
The random number draw is truly random (50% even, 50% odd).
However, you can try to detect patterns in opponent's CHOICES.

YOUR TASK:
Choose either "even" or "odd". Respond with ONLY the word "even" or "odd".
"""

    response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
        timeout=25.0  # Must respond within 25s (5s buffer for network)
    )

    choice = response.content[0].text.strip().lower()

    # Validate response
    if choice not in ["even", "odd"]:
        # Fallback to random if LLM returns invalid choice
        return random.choice(["even", "odd"])

    return choice
```

**Advantages:**
- Can analyze complex patterns humans might miss
- Provides natural language reasoning (useful for debugging)
- Impressive to demonstrate in class
- Can adapt to tournament context (e.g., "play safe if winning")

**Disadvantages:**
- Costs money (API calls)
- Slower (25s max vs instant for random)
- Doesn't statistically improve win rate (game is still random)
- Risk of timeout if API slow
- Requires fallback to simpler strategy if API fails

**Best Practices:**
- Set aggressive timeout (25s max, leaving 5s buffer)
- Always have fallback strategy (random or adaptive)
- Cache LLM responses to reduce API calls
- Use for interesting reasoning, not statistical advantage

---

### 8.2 Strategy Selection Meta-Logic

**Recommended Approach:**
```python
def choose_parity(match_id: str, opponent_id: str, game_history: list,
                  standings: list) -> str:
    """
    Meta-strategy: Choose which strategy to use based on context.

    Priority:
    1. Try LLM strategy (if enabled and API healthy)
    2. Fall back to adaptive strategy (if enough history)
    3. Fall back to random strategy (always works)
    """
    try:
        # Phase 3: LLM strategy (optional)
        if LLM_ENABLED and api_is_healthy():
            return choose_parity_llm(opponent_id, game_history, standings)
    except TimeoutError:
        logger.warning("LLM timeout, falling back to adaptive")
    except Exception as e:
        logger.error(f"LLM error: {e}, falling back to adaptive")

    try:
        # Phase 2: Adaptive strategy
        opp_history = [g for g in game_history if g["opponent_id"] == opponent_id]
        if len(opp_history) >= 5:
            return choose_parity_adaptive(opponent_id, game_history)
    except Exception as e:
        logger.error(f"Adaptive strategy error: {e}, falling back to random")

    # Phase 1: Random strategy (always works, never fails)
    return choose_parity_random()
```

---

## 9. Game Rules Module Architecture

### 9.1 Module Purpose

**Goal:** Separate game-specific logic from generic protocol logic to enable extensibility.

**Benefits:**
- **Extensibility:** Add new games (tic-tac-toe, chess) without changing protocol
- **Maintainability:** Game rules in one place, easy to update
- **Testability:** Unit test game logic independent of network protocol
- **Clarity:** Clear separation of concerns

---

### 9.2 Module Interface

**Abstract Base Class:**
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class GameRules(ABC):
    """
    Abstract interface for game-specific logic.
    All games must implement this interface.
    """

    @abstractmethod
    def get_game_type(self) -> str:
        """Return game type identifier (e.g., 'even_odd')"""
        pass

    @abstractmethod
    def get_valid_move_types(self) -> List[str]:
        """Return list of valid move types for this game"""
        pass

    @abstractmethod
    def init_game_state(self, player_a_id: str, player_b_id: str) -> Dict[str, Any]:
        """
        Initialize game-specific state.

        Returns:
            dict with initial game state
        """
        pass

    @abstractmethod
    def validate_move(self, move_data: Dict[str, Any], game_state: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate if a move is legal.

        Args:
            move_data: Player's move data
            game_state: Current game state

        Returns:
            (is_valid: bool, error_message: str)
        """
        pass

    @abstractmethod
    def apply_move(self, player_id: str, move_data: Dict[str, Any],
                   game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply a move to game state.

        Returns:
            updated game state
        """
        pass

    @abstractmethod
    def is_game_complete(self, game_state: Dict[str, Any]) -> bool:
        """Check if game has ended"""
        pass

    @abstractmethod
    def determine_winner(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine game outcome.

        Returns:
            {
                "winner": player_id or None,
                "result_type": "WIN" | "DRAW" | "TECHNICAL_LOSS",
                "reason": str,
                "points": {player_a: int, player_b: int}
            }
        """
        pass
```

---

### 9.3 Even/Odd Implementation

```python
import secrets
from typing import Any, Dict, List

class EvenOddRules(GameRules):
    """
    Implementation of Even/Odd game rules.
    """

    def get_game_type(self) -> str:
        return "even_odd"

    def get_valid_move_types(self) -> List[str]:
        return ["choose_parity"]

    def init_game_state(self, player_a_id: str, player_b_id: str) -> Dict[str, Any]:
        return {
            "player_a_id": player_a_id,
            "player_b_id": player_b_id,
            "player_a_choice": None,
            "player_b_choice": None,
            "drawn_number": None,
            "winner": None
        }

    def validate_move(self, move_data: Dict[str, Any], game_state: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate parity choice.

        Valid choices: exactly "even" or "odd" (lowercase string)
        """
        if "choice" not in move_data:
            return False, "Missing 'choice' field"

        choice = move_data["choice"]

        if not isinstance(choice, str):
            return False, f"Choice must be string, got {type(choice).__name__}"

        if choice not in ["even", "odd"]:
            return False, f"Choice must be 'even' or 'odd', got '{choice}'"

        return True, ""

    def apply_move(self, player_id: str, move_data: Dict[str, Any],
                   game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store player's choice in game state.
        """
        choice = move_data["choice"]

        if player_id == game_state["player_a_id"]:
            game_state["player_a_choice"] = choice
        elif player_id == game_state["player_b_id"]:
            game_state["player_b_choice"] = choice
        else:
            raise ValueError(f"Unknown player: {player_id}")

        return game_state

    def is_game_complete(self, game_state: Dict[str, Any]) -> bool:
        """
        Game is complete when both players have chosen.
        """
        return (game_state["player_a_choice"] is not None and
                game_state["player_b_choice"] is not None)

    def determine_winner(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draw random number and determine winner.
        """
        # Draw cryptographically secure random number
        drawn_number = secrets.randbelow(10) + 1
        game_state["drawn_number"] = drawn_number

        number_parity = "even" if drawn_number % 2 == 0 else "odd"

        choice_a = game_state["player_a_choice"]
        choice_b = game_state["player_b_choice"]
        player_a_id = game_state["player_a_id"]
        player_b_id = game_state["player_b_id"]

        # Case 1: Both chose the same
        if choice_a == choice_b:
            return {
                "winner": None,
                "result_type": "DRAW",
                "reason": f"Both chose {choice_a}, number was {drawn_number} ({number_parity})",
                "drawn_number": drawn_number,
                "number_parity": number_parity,
                "points": {player_a_id: 1, player_b_id: 1}
            }

        # Case 2: Different choices - determine winner
        if choice_a == number_parity:
            winner = player_a_id
        else:
            winner = player_b_id

        return {
            "winner": winner,
            "result_type": "WIN",
            "reason": f"Winner chose {number_parity}, number was {drawn_number} ({number_parity})",
            "drawn_number": drawn_number,
            "number_parity": number_parity,
            "points": {
                winner: 3,
                player_a_id if winner == player_b_id else player_b_id: 0
            }
        }
```

---

### 9.4 Module Integration with Referee

```python
class Referee:
    def __init__(self, game_type: str):
        # Load appropriate game rules module
        self.game_rules = self._load_game_rules(game_type)

    def _load_game_rules(self, game_type: str) -> GameRules:
        """
        Factory method to load game-specific rules.
        """
        if game_type == "even_odd":
            return EvenOddRules()
        elif game_type == "tic_tac_toe":
            return TicTacToeRules()  # Future implementation
        else:
            raise ValueError(f"Unknown game type: {game_type}")

    async def run_match(self, match_id: str, player_a_id: str, player_b_id: str):
        """
        Run a match using the loaded game rules.
        """
        # Initialize game state
        game_state = self.game_rules.init_game_state(player_a_id, player_b_id)

        # ... invitation and arrival phases ...

        # Collect moves
        for player_id in [player_a_id, player_b_id]:
            move_data = await self.request_move(player_id)

            # Validate move
            is_valid, error = self.game_rules.validate_move(move_data, game_state)
            if not is_valid:
                await self.send_error(player_id, "INVALID_MOVE", error)
                continue

            # Apply move
            game_state = self.game_rules.apply_move(player_id, move_data, game_state)

        # Check if game complete
        if self.game_rules.is_game_complete(game_state):
            # Determine winner
            result = self.game_rules.determine_winner(game_state)
            await self.report_result(result)
```

---

## 10. Extensibility to Other Games

### 10.1 Generic Message Abstraction

**Current:** Game-specific messages (CHOOSE_PARITY_CALL/RESPONSE)
**Future:** Generic messages (GAME_MOVE_CALL/RESPONSE)

**Mapping:**
| Specific Message | Generic Message |
|------------------|-----------------|
| CHOOSE_PARITY_CALL | GAME_MOVE_CALL |
| CHOOSE_PARITY_RESPONSE | GAME_MOVE_RESPONSE |

**Benefits:**
- Single message handler in referee code
- Player agents can support multiple games with one implementation
- Easier to add new games (no protocol changes needed)

---

### 10.2 Game Registry

**Purpose:** Central registry of supported games with metadata.

```python
GAME_REGISTRY = {
    "even_odd": {
        "display_name": "Even/Odd",
        "description": "Choose even or odd, random number determines winner",
        "move_types": ["choose_parity"],
        "valid_choices": {
            "choose_parity": ["even", "odd"]
        },
        "min_players": 2,
        "max_players": 2,
        "rules_class": "EvenOddRules",
        "avg_duration_seconds": 20
    },
    "tic_tac_toe": {
        "display_name": "Tic-Tac-Toe",
        "description": "Classic 3x3 grid game",
        "move_types": ["place_mark"],
        "valid_choices": {
            "place_mark": list(range(9))  # Positions 0-8
        },
        "min_players": 2,
        "max_players": 2,
        "rules_class": "TicTacToeRules",
        "avg_duration_seconds": 60
    }
}
```

**Use Cases:**
- Player registration: declare which games they support
- League creation: specify game type for tournament
- Validation: check if move is legal for game type
- UI: Display available games to users

---

### 10.3 Future Game Examples

**Tic-Tac-Toe:**
- Move: `{"move_type": "place_mark", "position": 4}`
- State: 9-cell grid, track X/O positions
- Winner: First to get 3 in a row

**Rock-Paper-Scissors:**
- Move: `{"move_type": "choose_gesture", "gesture": "rock"|"paper"|"scissors"}`
- State: Both player choices
- Winner: Rock beats scissors, scissors beats paper, paper beats rock

**21 Questions:**
- Move: `{"move_type": "ask_question", "question": "Is it bigger than a breadbox?"}`
- State: Question history, yes/no answers
- Winner: Guesser gets it right, or answerer survives 21 questions

---

## 11. User Stories

### US-1: Play Even/Odd Game
> **As a** player agent
> **I want to** choose "even" or "odd" in response to referee request
> **So that** I can participate in the game and try to win
>
> **Acceptance Criteria:**
> - Agent receives CHOOSE_PARITY_CALL message
> - Agent responds with "even" or "odd" within 30 seconds
> - Choice is validated and accepted by referee

### US-2: Learn from Game History
> **As a** player agent
> **I want to** receive complete game results (choices, number, outcome)
> **So that** I can analyze patterns and improve my strategy
>
> **Acceptance Criteria:**
> - GAME_OVER message includes both players' choices
> - Message includes the drawn number and parity
> - Message includes clear winner determination reason

### US-3: Implement Pattern Detection
> **As a** student developer
> **I want to** detect patterns in opponent behavior
> **So that** my agent can exploit non-random opponents
>
> **Acceptance Criteria:**
> - Agent stores game history per opponent
> - Agent performs statistical analysis (chi-squared test)
> - Agent adapts strategy based on detected patterns

### US-4: Fair Random Number Generation
> **As an** instructor
> **I want to** ensure random numbers are truly random
> **So that** no agent can gain unfair advantage through prediction
>
> **Acceptance Criteria:**
> - Referee uses cryptographically secure random (secrets module)
> - Statistical test: 10,000 draws show uniform distribution
> - No correlation between consecutive draws

### US-5: Extend to New Games
> **As a** system architect
> **I want to** add new games without changing core protocol
> **So that** the system is future-proof and maintainable
>
> **Acceptance Criteria:**
> - Game rules encapsulated in GameRules module
> - Generic GAME_MOVE messages work for any game
> - Game registry enables capability discovery

---

## 12. Acceptance Criteria

### 12.1 Game Rules
- ✅ Two players per match (exactly)
- ✅ Valid choices: only "even" or "odd" (lowercase)
- ✅ Random number: 1-10 inclusive, cryptographically secure
- ✅ Winner determination: correct according to rules
- ✅ Draw handling: both chose same → always draw

### 12.2 Game Flow
- ✅ All 6 phases execute in correct order
- ✅ Choices collected simultaneously (not sequentially)
- ✅ Number drawn after both choices received
- ✅ Result reported to both players and league manager

### 12.3 Timeouts
- ✅ Invitation response: 5 seconds
- ✅ Choice response: 30 seconds
- ✅ Result acknowledgment: 5 seconds (best-effort)
- ✅ Timeout triggers retry logic (max 3 attempts)

### 12.4 State Management
- ✅ State machine follows defined transitions
- ✅ State persisted for recovery
- ✅ Invalid state transitions prevented
- ✅ Terminal states (FINISHED, ABORTED) are final

### 12.5 Scoring
- ✅ Win = 3 points, Draw = 1 point, Loss = 0 points
- ✅ Technical loss = 0 points (same as normal loss)
- ✅ Standings updated immediately after each match
- ✅ Tiebreakers applied correctly

### 12.6 Randomness Quality
- ✅ Cryptographically secure random used
- ✅ Uniform distribution (chi-squared test p > 0.05)
- ✅ No autocorrelation between draws
- ✅ Each number 1-10 has 10% probability

### 12.7 Validation
- ✅ Invalid choices rejected with clear error
- ✅ Case-sensitive validation ("Even" ≠ "even")
- ✅ Type validation (must be string, not int)
- ✅ Retry allowed within timeout window

---

## 13. Success Metrics

### 13.1 Game Quality Metrics
- **Randomness Quality:** Chi-squared p-value > 0.05 for 1000+ games
- **Outcome Distribution:** ~50% Player A wins, ~50% Player B wins (with random strategies)
- **Draw Rate:** ~25% (when both choose same, which is 50% × 50%)
- **Technical Loss Rate:** < 5% (indicates timeout/error issues)

### 13.2 Performance Metrics
- **Average Game Duration:** < 20 seconds (typical case)
- **Max Game Duration:** < 45 seconds (worst case with timeouts)
- **State Transition Latency:** < 10ms (internal processing)
- **Random Number Generation:** < 1ms

### 13.3 Student Success Metrics
- **Implementation Success Rate:** > 95% of students implement working agent
- **Strategy Diversity:** > 3 distinct strategy types observed
- **Pattern Detection Accuracy:** > 70% true positive rate (against patterned opponents)
- **Student Satisfaction:** > 80% report game is "fair and educational"

### 13.4 System Reliability Metrics
- **Match Completion Rate:** > 98%
- **Referee Uptime:** > 99.9% during tournament
- **Data Integrity:** 0% data loss (all results persisted)
- **Audit Trail Completeness:** 100% of matches have complete logs

---

## 14. Technical Constraints

### 14.1 Randomness Requirements
- **Python:** `secrets.randbelow(10) + 1` (MANDATORY)
- **Statistical Quality:** Chi-squared p > 0.05
- **Independence:** No correlation between draws

### 14.2 Choice Validation
- **Allowed Values:** Exactly `"even"` or `"odd"`
- **Case:** Lowercase only
- **Type:** String only (not int, bool, or null)

### 14.3 Timeout Limits
- Invitation: 5 seconds
- Choice: 30 seconds
- Acknowledgment: 5 seconds
- Retry delay: 2 seconds

### 14.4 State Persistence
- **Format:** JSON or SQLite
- **Update Frequency:** After each state transition
- **Retention:** Minimum 30 days
- **Recovery:** Must support referee restart

### 14.5 Concurrency
- **Simultaneous Choice Collection:** MANDATORY
- **Race Condition Handling:** Use locks/transactions
- **Timeout Enforcement:** Per-player, not total

---

## 15. Risk Assessment

### 15.1 High-Priority Risks

**Risk: Weak Randomness Allows Prediction**
- **Impact:** Critical (breaks game fairness)
- **Mitigation:** Use `secrets` module, statistical validation, code review

**Risk: Sequential Choice Collection (Unfair Advantage)**
- **Impact:** High (second player gets timing info)
- **Mitigation:** Explicit requirement for simultaneity, integration tests

**Risk: Students Can't Implement Strategies**
- **Impact:** High (educational goal not met)
- **Mitigation:** Provide reference implementations, office hours, examples

### 15.2 Medium-Priority Risks

**Risk: Pattern Detection Overfitting to Noise**
- **Impact:** Medium (agents underperform against random opponents)
- **Mitigation:** Teach statistical significance, require minimum sample size

**Risk: LLM Strategy Timeouts**
- **Impact:** Medium (technical losses)
- **Mitigation:** Mandatory fallback to simpler strategy, aggressive timeout

### 15.3 Low-Priority Risks

**Risk: Draw Rate Too High (Boring)**
- **Impact:** Low (still educational)
- **Mitigation:** Accept as inherent to game design

---

**Document Status:** DRAFT - Pending Review
**Next Review Date:** 2025-12-27
**Approvers:** Course Instructor, Technical Lead, Game Design Expert
