# Message Envelope Design

**Document Type:** Architecture Design
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** All Agent Developers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Envelope Structure](#2-envelope-structure)
3. [Required Fields](#3-required-fields)
4. [Optional Fields](#4-optional-fields)
5. [UTC Timezone Enforcement](#5-utc-timezone-enforcement)
6. [Validation Rules](#6-validation-rules)
7. [Implementation](#7-implementation)
8. [Examples by Message Type](#8-examples-by-message-type)

---

## 1. Introduction

All messages in the Even/Odd League system use a **standard envelope** structure. This envelope provides:
- **Protocol versioning** for compatibility
- **Message typing** for routing
- **Sender identification** for security
- **Timestamps** for debugging and audit trails
- **Conversation tracking** for distributed tracing

### 1.1 Design Principles

1. **Uniformity:** All 18 message types use the same envelope structure
2. **Traceability:** `conversation_id` links related messages
3. **UTC-Only:** All timestamps in UTC timezone (no local times)
4. **Validation:** Strict schema validation on all fields

---

## 2. Envelope Structure

```json
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

  ... message-specific fields ...
}
```

---

## 3. Required Fields

All messages MUST include these fields:

### 3.1 protocol

- **Type:** `string`
- **Format:** `"league.v{major}.{minor}"` (semantic versioning)
- **Current Value:** `"league.v2"`
- **Purpose:** Protocol version for compatibility checking

**Example:**
```json
{"protocol": "league.v2"}
```

### 3.2 message_type

- **Type:** `string`
- **Format:** UPPER_SNAKE_CASE
- **Values:** One of 18 defined message types
- **Purpose:** Message routing and handler selection

**Valid Message Types:**

| Category | Message Types |
|----------|---------------|
| Registration | `REFEREE_REGISTER_REQUEST`, `REFEREE_REGISTER_RESPONSE`, `LEAGUE_REGISTER_REQUEST`, `LEAGUE_REGISTER_RESPONSE` |
| League Management | `ROUND_ANNOUNCEMENT`, `ROUND_COMPLETED`, `LEAGUE_STANDINGS_UPDATE`, `LEAGUE_COMPLETED`, `LEAGUE_QUERY` |
| Game Flow | `GAME_INVITATION`, `GAME_JOIN_ACK`, `CHOOSE_PARITY_CALL`, `CHOOSE_PARITY_RESPONSE`, `GAME_OVER` |
| Reporting | `MATCH_RESULT_REPORT` |
| Errors | `LEAGUE_ERROR`, `GAME_ERROR` |

**Example:**
```json
{"message_type": "GAME_INVITATION"}
```

### 3.3 sender

- **Type:** `string`
- **Format:** `"{agent_type}:{agent_id}"` or `"{agent_type}"`
- **Purpose:** Identify message originator

**Agent Types:**
- `"league_manager"` - League Manager (no agent_id suffix)
- `"referee:{referee_id}"` - Referee (e.g., `"referee:REF01"`)
- `"player:{player_id}"` - Player (e.g., `"player:P01"`)

**Before Registration:**
- Players/Referees use temporary names: `"player:alpha"`, `"referee:beta"`
- After registration, use assigned IDs: `"player:P01"`, `"referee:REF01"`

**Example:**
```json
{"sender": "referee:REF01"}
```

### 3.4 timestamp

- **Type:** `string`
- **Format:** ISO 8601 in UTC timezone
- **Pattern:** `YYYYMMDDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS+00:00`
- **Purpose:** Message creation time for ordering and debugging

**CRITICAL:** Must be in UTC timezone (Z suffix or +00:00 offset).

**Valid Examples:**
```json
{"timestamp": "20250115T10:30:00Z"}
{"timestamp": "2025-01-15T10:30:00Z"}
{"timestamp": "2025-01-15T10:30:00+00:00"}
```

**Invalid Examples:**
```json
{"timestamp": "20250115T10:30:00+02:00"}  // ✗ Local timezone
{"timestamp": "20250115T10:30:00"}        // ✗ No timezone
{"timestamp": "2025-01-15 10:30:00"}      // ✗ Wrong format
```

### 3.5 conversation_id

- **Type:** `string`
- **Format:** Unique identifier (no specific pattern required)
- **Purpose:** Link related messages in a conversation

**Conversation Scope:**
- **Registration:** One conversation per agent registration
- **Match:** One conversation per match (shared by all messages in that match)
- **Round:** One conversation per round announcement
- **Error:** Inherits from triggering message

**Naming Convention (Recommended):**
- Registration: `"conv{agenttype}{id}reg{seq}"`
- Match: `"conv{match_id}{seq}"`
- Round: `"convround{round_id}{type}"`

**Example:**
```json
{"conversation_id": "convr1m1001"}
```

**Match Message Flow (Same conversation_id):**
1. `GAME_INVITATION` → `conversation_id: "convr1m1001"`
2. `GAME_JOIN_ACK` → `conversation_id: "convr1m1001"`
3. `CHOOSE_PARITY_CALL` → `conversation_id: "convr1m1001"`
4. `CHOOSE_PARITY_RESPONSE` → `conversation_id: "convr1m1001"`
5. `GAME_OVER` → `conversation_id: "convr1m1001"`

---

## 4. Optional Fields

These fields are included based on message type:

### 4.1 auth_token

- **Type:** `string`
- **When Required:** All messages **after** registration (except registration requests)
- **Purpose:** Authentication and authorization
- **Format:** Opaque token (e.g., `"tok_p01_xyz789"`)

**Example:**
```json
{"auth_token": "tok_p01_xyz789"}
```

### 4.2 league_id

- **Type:** `string`
- **When Required:** All league and game messages
- **Purpose:** Identify which league this message belongs to
- **Format:** Typically `"league_{year}_{game_type}"`

**Example:**
```json
{"league_id": "league_2025_even_odd"}
```

### 4.3 round_id

- **Type:** `integer`
- **When Required:** Round and match messages
- **Purpose:** Identify tournament round
- **Range:** 1 to total_rounds

**Example:**
```json
{"round_id": 1}
```

### 4.4 match_id

- **Type:** `string`
- **When Required:** All game flow messages
- **Purpose:** Unique match identifier
- **Format:** Typically `"R{round}M{match}"`

**Example:**
```json
{"match_id": "R1M1"}
```

---

## 5. UTC Timezone Enforcement

**CRITICAL REQUIREMENT:** All timestamps MUST be in UTC timezone.

### 5.1 Why UTC Only?

- **Distributed System:** Agents may run in different timezones
- **Log Correlation:** Easier to correlate events across agents
- **Avoid Ambiguity:** No DST transitions, timezone confusion

### 5.2 Valid UTC Formats

| Format | Example | Valid? |
|--------|---------|--------|
| ISO 8601 with Z | `"2025-01-15T10:30:00Z"` | ✓ |
| ISO 8601 compact with Z | `"20250115T103000Z"` | ✓ |
| ISO 8601 with +00:00 | `"2025-01-15T10:30:00+00:00"` | ✓ |
| ISO 8601 with local TZ | `"2025-01-15T10:30:00+02:00"` | ✗ |
| No timezone | `"2025-01-15T10:30:00"` | ✗ |

### 5.3 Implementation

```python
from datetime import datetime, timezone

def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()

# Returns: "2025-01-15T10:30:00.123456+00:00"
```

**Compact format (no milliseconds):**

```python
def get_utc_timestamp_compact() -> str:
    """Get UTC timestamp without milliseconds."""
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

# Returns: "20250115T103000Z"
```

### 5.4 Validation

```python
from datetime import datetime

def is_valid_utc_timestamp(timestamp_str: str) -> bool:
    """Validate UTC timestamp format."""
    try:
        # Parse timestamp
        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

        # Check if UTC (offset is 0)
        if dt.utcoffset().total_seconds() != 0:
            return False

        return True
    except (ValueError, AttributeError):
        return False

# Tests
assert is_valid_utc_timestamp("2025-01-15T10:30:00Z") == True
assert is_valid_utc_timestamp("2025-01-15T10:30:00+00:00") == True
assert is_valid_utc_timestamp("2025-01-15T10:30:00+02:00") == False
assert is_valid_utc_timestamp("2025-01-15T10:30:00") == False
```

---

## 6. Validation Rules

### 6.1 Envelope Validator

```python
from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime

class MessageEnvelope(BaseModel):
    """
    Base message envelope validator.
    All message types inherit from this.
    """
    protocol: str = Field(..., regex=r"^league\.v\d+$")
    message_type: str = Field(..., regex=r"^[A-Z_]+$")
    sender: str = Field(..., regex=r"^(league_manager|referee:\w+|player:\w+)$")
    timestamp: str
    conversation_id: str = Field(..., min_length=1, max_length=100)

    # Optional fields
    auth_token: Optional[str] = None
    league_id: Optional[str] = None
    round_id: Optional[int] = Field(None, ge=1)
    match_id: Optional[str] = None

    @validator('timestamp')
    def validate_utc_timestamp(cls, v):
        """Ensure timestamp is in UTC timezone."""
        try:
            # Parse timestamp
            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))

            # Check UTC
            if dt.utcoffset().total_seconds() != 0:
                raise ValueError("Timestamp must be in UTC timezone")

            return v
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid timestamp format: {str(e)}")

    @validator('message_type')
    def validate_message_type(cls, v):
        """Validate message type is one of the defined types."""
        valid_types = {
            "REFEREE_REGISTER_REQUEST", "REFEREE_REGISTER_RESPONSE",
            "LEAGUE_REGISTER_REQUEST", "LEAGUE_REGISTER_RESPONSE",
            "ROUND_ANNOUNCEMENT", "ROUND_COMPLETED",
            "LEAGUE_STANDINGS_UPDATE", "LEAGUE_COMPLETED", "LEAGUE_QUERY",
            "GAME_INVITATION", "GAME_JOIN_ACK",
            "CHOOSE_PARITY_CALL", "CHOOSE_PARITY_RESPONSE",
            "GAME_OVER", "MATCH_RESULT_REPORT",
            "LEAGUE_ERROR", "GAME_ERROR"
        }
        if v not in valid_types:
            raise ValueError(f"Invalid message_type: {v}")
        return v
```

### 6.2 Usage in Message Schemas

```python
class GameInvitation(MessageEnvelope):
    """Specific message schema inheriting from envelope."""
    message_type: str = Field(default="GAME_INVITATION", const=True)
    auth_token: str = Field(..., min_length=1)
    league_id: str = Field(..., min_length=1)
    round_id: int = Field(..., ge=1)
    match_id: str = Field(..., min_length=1)
    game_type: str
    role_in_match: str = Field(..., regex=r"^(PLAYER_A|PLAYER_B)$")
    opponent_id: str

# Validation example
data = {
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

invitation = GameInvitation(**data)  # Validates all fields
```

---

## 7. Implementation

### 7.1 Envelope Builder

```python
from datetime import datetime, timezone
from typing import Optional

class EnvelopeBuilder:
    """Helper for constructing message envelopes."""

    def __init__(self, agent_id: str, agent_type: str):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.sender = f"{agent_type}:{agent_id}" if agent_id else agent_type

    def create_envelope(
        self,
        message_type: str,
        conversation_id: str,
        auth_token: Optional[str] = None,
        league_id: Optional[str] = None,
        round_id: Optional[int] = None,
        match_id: Optional[str] = None
    ) -> dict:
        """Create a message envelope with required fields."""
        envelope = {
            "protocol": "league.v2",
            "message_type": message_type,
            "sender": self.sender,
            "timestamp": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
            "conversation_id": conversation_id
        }

        # Add optional fields if provided
        if auth_token:
            envelope["auth_token"] = auth_token
        if league_id:
            envelope["league_id"] = league_id
        if round_id is not None:
            envelope["round_id"] = round_id
        if match_id:
            envelope["match_id"] = match_id

        return envelope

# Usage
builder = EnvelopeBuilder(agent_id="P01", agent_type="player")

envelope = builder.create_envelope(
    message_type="CHOOSE_PARITY_RESPONSE",
    conversation_id="convr1m1001",
    auth_token="tok_p01_xyz789",
    league_id="league_2025_even_odd",
    round_id=1,
    match_id="R1M1"
)
```

---

## 8. Examples by Message Type

### 8.1 Registration Messages

**REFEREE_REGISTER_REQUEST:**
```json
{
  "protocol": "league.v2",
  "message_type": "REFEREE_REGISTER_REQUEST",
  "sender": "referee:alpha",
  "timestamp": "20250115T10:00:00Z",
  "conversation_id": "convrefalphareg001"
}
```

**LEAGUE_REGISTER_RESPONSE:**
```json
{
  "protocol": "league.v2",
  "message_type": "LEAGUE_REGISTER_RESPONSE",
  "sender": "league_manager",
  "timestamp": "20250115T10:05:01Z",
  "conversation_id": "convplayeralphareg001",
  "league_id": "league_2025_even_odd"
}
```

### 8.2 Game Flow Messages

**GAME_INVITATION:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_INVITATION",
  "sender": "referee:REF01",
  "timestamp": "20250115T10:15:00Z",
  "conversation_id": "convr1m1001",
  "auth_token": "tok_ref01_abc123",
  "league_id": "league_2025_even_odd",
  "round_id": 1,
  "match_id": "R1M1"
}
```

**CHOOSE_PARITY_RESPONSE:**
```json
{
  "protocol": "league.v2",
  "message_type": "CHOOSE_PARITY_RESPONSE",
  "sender": "player:P01",
  "timestamp": "20250115T10:15:10Z",
  "conversation_id": "convr1m1001",
  "auth_token": "tok_p01_xyz789",
  "match_id": "R1M1"
}
```

### 8.3 Error Messages

**GAME_ERROR:**
```json
{
  "protocol": "league.v2",
  "message_type": "GAME_ERROR",
  "sender": "referee:REF01",
  "timestamp": "20250115T10:16:00Z",
  "conversation_id": "convr1m1001",
  "match_id": "R1M1"
}
```

---

## Summary

The message envelope provides:

✅ **Protocol versioning** (`protocol: "league.v2"`)
✅ **Message typing** (`message_type: "GAME_INVITATION"`)
✅ **Sender identification** (`sender: "referee:REF01"`)
✅ **UTC timestamps** (`timestamp: "20250115T10:15:00Z"`)
✅ **Conversation tracking** (`conversation_id: "convr1m1001"`)
✅ **Authentication** (`auth_token: "tok_ref01_abc123"`)
✅ **Context fields** (`league_id`, `round_id`, `match_id`)

All agents MUST validate the envelope before processing message-specific fields.

---

**Related Documents:**
- `common-design.md` - MCP server and error handling patterns
- `authentication-design.md` - Auth token lifecycle
- `game-protocol-messages-prd.md` - Complete catalog of 18 message types

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
