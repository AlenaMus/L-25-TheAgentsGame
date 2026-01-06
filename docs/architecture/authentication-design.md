# Authentication Design

**Document Type:** Architecture Design
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL
**Target Audience:** All Agent Developers

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Token Lifecycle](#2-token-lifecycle)
3. [Token Generation](#3-token-generation)
4. [Token Storage](#4-token-storage)
5. [Token Validation](#5-token-validation)
6. [Error Handling](#6-error-handling)
7. [Security Best Practices](#7-security-best-practices)
8. [Implementation](#8-implementation)

---

## 1. Introduction

The Even/Odd League system uses **token-based authentication** for all inter-agent communication after registration.

### 1.1 Authentication Flow

```
┌─────────────┐                    ┌──────────────────┐
│   Agent     │  1. Register       │  League Manager  │
│ (Unauth)    │ ────────────────>  │                  │
│             │                    │                  │
│             │  2. auth_token     │                  │
│             │  <────────────────  │                  │
│             │                    │                  │
│   Agent     │  3. All requests   │                  │
│ (Authed)    │  include token ──> │  Validates token │
└─────────────┘                    └──────────────────┘
```

### 1.2 Design Goals

1. **Simplicity:** Opaque tokens (not JWT) - stateful validation
2. **Security:** Cryptographically secure token generation
3. **Auditability:** Token usage logged for debugging
4. **Fail-Safe:** Invalid token = immediate rejection (no silent failures)

---

## 2. Token Lifecycle

### 2.1 Lifecycle Stages

```
┌────────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Generation │ -> │ Storage  │ -> │  Usage   │ -> │ Expiry   │
│            │    │          │    │          │    │(Optional)│
└────────────┘    └──────────┘    └──────────┘    └──────────┘
```

**Stage 1: Generation**
- League Manager generates unique token during registration
- Format: `"tok_{agent_type}{agent_id}_{random}"`
- Example: `"tok_p01_xyz789"`

**Stage 2: Storage**
- League Manager: Stores `agent_id → auth_token` mapping
- Agent: Stores received token locally

**Stage 3: Usage**
- Agent: Includes token in `auth_token` field of all requests
- League Manager/Referee: Validates token before processing

**Stage 4: Expiry** (Optional - not implemented in current version)
- Tokens could expire after tournament ends
- Renewal mechanism for long tournaments

### 2.2 Token Scope

| Token Type | Issued By | Used By | Valid For |
|------------|-----------|---------|-----------|
| Player Token | League Manager | Player Agent | All league and game operations |
| Referee Token | League Manager | Referee | Game operations and result reporting |

**Note:** League Manager doesn't need a token (it's the authority).

---

## 3. Token Generation

### 3.1 Requirements

1. **Uniqueness:** Each agent gets a unique token
2. **Unpredictability:** Tokens must be cryptographically random
3. **Sufficient Entropy:** At least 128 bits of randomness
4. **Readability:** Human-readable format for debugging

### 3.2 Implementation

```python
"""
Secure token generation.
"""

import secrets
import string

def generate_auth_token(agent_type: str, agent_id: str, length: int = 16) -> str:
    """
    Generate a cryptographically secure authentication token.

    Args:
        agent_type: "player" or "referee"
        agent_id: Assigned agent ID (e.g., "P01", "REF01")
        length: Length of random suffix (default: 16 characters)

    Returns:
        Token string (e.g., "tok_p01_abc123xyz789")

    Security:
        Uses secrets module (CSPRNG) for cryptographic randomness.
    """
    # Create alphabet (lowercase + digits)
    alphabet = string.ascii_lowercase + string.digits

    # Generate random suffix
    random_suffix = ''.join(secrets.choice(alphabet) for _ in range(length))

    # Format: tok_{type}{id}_{random}
    agent_prefix = agent_type[0].lower() + agent_id.lower()
    token = f"tok_{agent_prefix}_{random_suffix}"

    return token

# Examples
generate_auth_token("player", "P01")   # → "tok_p01_abc123xyz789..."
generate_auth_token("referee", "REF01") # → "tok_refref01_xyz789abc123..."
```

### 3.3 Token Format

**Pattern:** `tok_{agent_prefix}_{random_suffix}`

**Components:**
- `tok_` - Fixed prefix for easy identification
- `{agent_prefix}` - Agent type initial + ID (e.g., `p01`, `refref01`)
- `_` - Separator
- `{random_suffix}` - 16+ characters of random data

**Examples:**

| Agent Type | Agent ID | Token Example |
|------------|----------|---------------|
| Player | P01 | `tok_p01_x7k9m2n5p8q1r4t6` |
| Player | P02 | `tok_p02_a3b6c9d2e5f8g1h4` |
| Referee | REF01 | `tok_refref01_z9y8x7w6v5u4t3` |
| Referee | REF02 | `tok_refref02_s2r1q0p9o8n7m6` |

---

## 4. Token Storage

### 4.1 League Manager Storage

League Manager maintains an in-memory map: `agent_id → token`

```python
"""
Token storage in League Manager.
"""

from typing import Dict

class TokenStore:
    """In-memory token storage."""

    def __init__(self):
        self.player_tokens: Dict[str, str] = {}  # player_id → token
        self.referee_tokens: Dict[str, str] = {}  # referee_id → token

    def store_player_token(self, player_id: str, token: str):
        """Store a player's auth token."""
        self.player_tokens[player_id] = token

    def store_referee_token(self, referee_id: str, token: str):
        """Store a referee's auth token."""
        self.referee_tokens[referee_id] = token

    def validate_player_token(self, player_id: str, token: str) -> bool:
        """Validate a player's token."""
        return self.player_tokens.get(player_id) == token

    def validate_referee_token(self, referee_id: str, token: str) -> bool:
        """Validate a referee's token."""
        return self.referee_tokens.get(referee_id) == token

    def get_all_tokens(self) -> dict:
        """Get all tokens (for debugging/backup)."""
        return {
            "players": self.player_tokens.copy(),
            "referees": self.referee_tokens.copy()
        }
```

### 4.2 Agent Storage

Agents store their token in configuration or state.

```python
"""
Token storage in Player/Referee agents.
"""

class AgentConfig:
    """Agent configuration including auth token."""

    def __init__(self):
        self.agent_id: str = None
        self.auth_token: str = None
        self.league_id: str = None

    def set_credentials(self, agent_id: str, auth_token: str, league_id: str):
        """Store credentials received during registration."""
        self.agent_id = agent_id
        self.auth_token = auth_token
        self.league_id = league_id

    def get_auth_header(self) -> dict:
        """Get authentication header for requests."""
        if not self.auth_token:
            raise ValueError("Not authenticated - register first")
        return {"auth_token": self.auth_token}

# Usage
config = AgentConfig()

# After registration
config.set_credentials(
    agent_id="P01",
    auth_token="tok_p01_xyz789",
    league_id="league_2025_even_odd"
)

# Include in requests
headers = config.get_auth_header()  # {"auth_token": "tok_p01_xyz789"}
```

---

## 5. Token Validation

### 5.1 Validation Rules

**When to validate:**
- All requests AFTER registration
- Before processing any tool call
- Before allowing access to protected resources

**Validation steps:**
1. Extract `auth_token` from request
2. Extract `sender` to identify agent
3. Look up expected token for that agent
4. Compare provided token with stored token
5. Reject if mismatch or missing

### 5.2 Implementation

```python
"""
Token validation middleware.
"""

from typing import Optional
from errors import GameError, ErrorCode

class AuthValidator:
    """Token validation for League Manager and Referees."""

    def __init__(self, token_store: TokenStore):
        self.token_store = token_store

    def validate_player_request(self, sender: str, auth_token: Optional[str]) -> bool:
        """
        Validate a player request.

        Args:
            sender: Sender field (e.g., "player:P01")
            auth_token: Provided token

        Returns:
            True if valid, raises exception if invalid
        """
        # Extract player_id from sender
        if not sender.startswith("player:"):
            raise ValueError(f"Invalid sender format: {sender}")

        player_id = sender.split(":", 1)[1]

        # Check token provided
        if not auth_token:
            raise GameError(
                code=ErrorCode.AUTH_TOKEN_MISSING,
                description="Missing auth_token",
                context={"sender": sender}
            )

        # Validate token
        if not self.token_store.validate_player_token(player_id, auth_token):
            raise GameError(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                description="Invalid auth_token",
                context={"sender": sender, "provided_token": auth_token[:8] + "..."}
            )

        return True

    def validate_referee_request(self, sender: str, auth_token: Optional[str]) -> bool:
        """Validate a referee request."""
        if not sender.startswith("referee:"):
            raise ValueError(f"Invalid sender format: {sender}")

        referee_id = sender.split(":", 1)[1]

        if not auth_token:
            raise GameError(
                code=ErrorCode.AUTH_TOKEN_MISSING,
                description="Missing auth_token"
            )

        if not self.token_store.validate_referee_token(referee_id, auth_token):
            raise GameError(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                description="Invalid auth_token"
            )

        return True
```

### 5.3 Usage in MCP Tools

```python
@app.post("/mcp")
async def mcp_endpoint(request: dict):
    """MCP endpoint with authentication."""
    params = request.get("params", {})
    method = request.get("method")

    # Skip auth for registration requests
    if method in ["register_player", "register_referee"]:
        return await handle_registration(params)

    # Validate authentication
    try:
        auth_validator.validate_player_request(
            sender=params.get("sender"),
            auth_token=params.get("auth_token")
        )
    except GameError as e:
        return {
            "jsonrpc": "2.0",
            "error": {
                "code": -32000,
                "message": e.description,
                "data": e.context
            },
            "id": request.get("id")
        }

    # Proceed with tool execution
    return await execute_tool(method, params)
```

---

## 6. Error Handling

### 6.1 Authentication Error Codes

| Error Code | Description | Cause | Action |
|------------|-------------|-------|--------|
| E011 | AUTH_TOKEN_MISSING | Request missing `auth_token` field | Include token in request |
| E012 | AUTH_TOKEN_INVALID | Token doesn't match stored token | Re-register |
| E013 | AUTH_TOKEN_EXPIRED | Token has expired (future feature) | Renew token |

### 6.2 Error Response Format

**LEAGUE_ERROR for authentication failures:**

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

### 6.3 Client-Side Error Handling

```python
async def call_with_auth_retry(endpoint: str, method: str, params: dict):
    """Call MCP tool with automatic re-registration on auth failure."""
    try:
        response = await mcp_client.call_tool(endpoint, method, params)

        # Check for auth error
        if "error" in response and response["error"].get("code") == -32000:
            error_data = response["error"].get("data", {})
            if error_data.get("error_code") == "E012":
                logging.warning("Auth token invalid, re-registering...")
                await re_register()
                # Retry with new token
                params["auth_token"] = config.auth_token
                return await mcp_client.call_tool(endpoint, method, params)

        return response
    except Exception as e:
        logging.error(f"Call failed: {str(e)}")
        raise
```

---

## 7. Security Best Practices

### 7.1 Token Security

**DO:**
- ✅ Use `secrets` module (not `random`) for generation
- ✅ Use minimum 16 characters of random data
- ✅ Validate tokens on EVERY request (except registration)
- ✅ Log authentication failures for audit
- ✅ Redact tokens in logs (show only first 8 characters)

**DON'T:**
- ❌ Don't use predictable tokens (sequential IDs, timestamps)
- ❌ Don't share tokens between agents
- ❌ Don't log full tokens in plaintext
- ❌ Don't accept requests without tokens (except registration)

### 7.2 Logging Tokens Safely

```python
def redact_token(token: str) -> str:
    """Redact token for safe logging."""
    if len(token) <= 8:
        return "***"
    return token[:8] + "..."

# Logging example
logger.info(
    "Request received",
    auth_token=redact_token(params["auth_token"])  # "tok_p01_..."
)
```

### 7.3 Token Transmission

- **Always use HTTPS in production** (localhost HTTP is OK for development)
- Tokens transmitted in JSON body (not URL parameters)
- No caching of authenticated responses

---

## 8. Implementation

### 8.1 Complete Registration Flow

**Referee Registration:**

```python
# League Manager side
async def handle_referee_registration(params: dict):
    """Handle referee registration request."""
    referee_meta = params["referee_meta"]
    display_name = referee_meta["display_name"]

    # Generate agent_id
    referee_id = generate_referee_id()  # "REF01"

    # Generate auth token
    auth_token = generate_auth_token("referee", referee_id)

    # Store token
    token_store.store_referee_token(referee_id, auth_token)

    # Store referee metadata
    referees[referee_id] = {
        "display_name": display_name,
        "endpoint": referee_meta["contact_endpoint"],
        "auth_token": auth_token
    }

    # Return credentials
    return {
        "protocol": "league.v2",
        "message_type": "REFEREE_REGISTER_RESPONSE",
        "status": "ACCEPTED",
        "referee_id": referee_id,
        "auth_token": auth_token,
        "league_id": "league_2025_even_odd"
    }

# Referee side
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
                "contact_endpoint": "http://localhost:8001/mcp"
            }
        }
    )

    # Store credentials
    result = response["result"]
    config.set_credentials(
        agent_id=result["referee_id"],
        auth_token=result["auth_token"],
        league_id=result["league_id"]
    )

    logger.info(
        "Registration successful",
        referee_id=config.agent_id,
        auth_token=redact_token(config.auth_token)
    )
```

---

## Summary

The authentication system provides:

✅ **Secure token generation** using `secrets` module
✅ **Simple token format** (`tok_{prefix}_{random}`)
✅ **Stateful validation** (League Manager stores tokens)
✅ **Clear error handling** (E011, E012, E013)
✅ **Audit trail** (all auth failures logged)
✅ **No silent failures** (invalid token = immediate rejection)

All agents MUST validate auth tokens on every request (except registration).

---

**Related Documents:**
- `common-design.md` - Error handling patterns
- `message-envelope-design.md` - Where auth_token appears in messages
- `league-manager-architecture.md` - Token generation and validation

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
