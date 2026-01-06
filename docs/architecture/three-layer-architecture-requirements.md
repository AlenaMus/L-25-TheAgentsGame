# Product Requirements Document (PRD)
# Three-Layer Architecture - Configuration, Runtime Data, and Logs

**Document Version:** 1.0  
**Date:** 2025-12-20  
**Status:** Final  
**Product Owner:** AI Development Course Team  
**Target Release:** Phase 1 - Foundation  
**Related Documents:**
- `league-system-prd.md` (League Management System)
- `implementation-architecture-prd.md` (Implementation Architecture)
- `game-protocol-messages-prd.md` (Protocol Messages)

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Architecture Philosophy](#architecture-philosophy)
3. [Layer 1: Configuration Layer](#layer-1-configuration-layer-config)
4. [Layer 2: Runtime Data Layer](#layer-2-runtime-data-layer-data)
5. [Layer 3: Logs Layer](#layer-3-logs-layer-logs)
6. [Cross-Layer Patterns](#cross-layer-patterns)
7. [Data Management Best Practices](#data-management-best-practices)
8. [Integration Points](#integration-points)
9. [User Stories](#user-stories)
10. [Acceptance Criteria](#acceptance-criteria)
11. [Success Metrics](#success-metrics)

---

## 1. Executive Summary

### 1.1 Problem Statement
Game developers need a clear, scalable architecture for managing configuration, runtime state, and logs across a distributed tournament system with thousands of agents, multiple leagues, and concurrent matches. Without a standardized structure, data becomes scattered, inconsistent, and unmaintainable.

### 1.2 Solution Overview
Implement a **Three-Layer Architecture** that separates concerns into:
- **Configuration Layer (config/)**: Static system settings (the "genetic code")
- **Runtime Data Layer (data/)**: Dynamic game state and historical records (the "memory")
- **Logs Layer (logs/)**: Observability and debugging traces (the "nervous system")

### 1.3 Key Benefits
- **Clear Separation of Concerns**: Developers know exactly where to put and find data
- **Scalability**: Architecture supports thousands of agents without performance degradation
- **Maintainability**: Schema versioning enables safe migrations
- **Debuggability**: Structured logs and data enable rapid issue diagnosis
- **Reliability**: Consistent patterns reduce bugs and data corruption
- **Testability**: Each layer can be tested independently

### 1.4 Guiding Principles
1. **Every file has a unique identifier (id)**
2. **Every file has a schema version (schema_version)**
3. **Every file has a timestamp (last_updated) in UTC/ISO8601**
4. **Protocol compliance to league.v2**
5. **Order, consistency, and trackability in all data**

---

## 2. Architecture Philosophy

### 2.1 The "Living System" Analogy

```
┌────────────────────────────────────────────────────────────┐
│                    LIVING SYSTEM                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CONFIG/ - GENETIC CODE (DNA)                        │  │
│  │  • Defines system structure and capabilities         │  │
│  │  • Read at startup (rarely changes)                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓ configures                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  DATA/ - MEMORY (Brain & Storage)                    │  │
│  │  • Stores experiences and current state              │  │
│  │  • Changes constantly during operation               │  │
│  └──────────────────────────────────────────────────────┘  │
│                          ↓ generates                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  LOGS/ - NERVOUS SYSTEM (Sensory Feedback)           │  │
│  │  • Tracks all actions and reactions                  │  │
│  │  • Append-only, immutable history                    │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

### 2.2 Design Principles

**1. Immutability Where Possible**
- Config files: Read-only after startup
- Logs: Append-only, never modified
- Data: Mutable, but with versioning

**2. Single Source of Truth**
- Each piece of data exists in exactly one place
- Derived data is computed, not stored redundantly
- Cross-references use IDs, not data duplication

**3. Fail-Safe Defaults**
- Missing config → load defaults and warn
- Corrupted data → restore from backup
- Log errors → continue operation (don't crash)

**4. Schema Evolution**
- Schema version in every file enables migrations
- Backward compatibility within major versions
- Migration scripts for schema upgrades

**5. Performance Through Simplicity**
- JSON files for small datasets (< 10,000 records)
- JSON Lines for streaming and large datasets
- Database upgrade path when needed


---

## 3. Layer 1: Configuration Layer (config/)

### 3.1 Overview

**Purpose**: Define the static structure and capabilities of the system.

**Philosophy**: This is the "genetic code" - it defines what the system *is* and what it *can do*, not what it *has done*.

**Access Pattern**: Read once at startup, cached in memory during runtime.

### 3.2 Directory Structure

```
config/
├── system.json                    # Core system settings
├── agents_config.json             # Agent type definitions
├── leagues/                       # League configurations
│   ├── league_even_odd_2025.json
│   ├── league_tictactoe_2025.json
│   └── defaults.json              # Default league settings
├── games/                         # Game type registry
│   ├── even_odd.json
│   ├── tictactoe.json
│   └── registry.json              # Game type catalog
└── defaults/                      # System-wide defaults
    ├── timeouts.json
    ├── ports.json
    └── retry_policies.json
```

### 3.3 Schema: system.json

**Purpose**: Core system configuration that applies globally.

```json
{
  "id": "system_config",
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T10:00:00Z",
  "protocol_version": "league.v2.1.0",
  
  "system": {
    "environment": "production",
    "log_level": "INFO",
    "enable_metrics": true,
    "enable_health_checks": true
  },
  
  "network": {
    "league_manager_host": "localhost",
    "league_manager_port": 8000,
    "referee_port_start": 8001,
    "referee_port_end": 8010,
    "player_port_start": 8101,
    "player_port_end": 8150
  },
  
  "timeouts": {
    "registration": 10,
    "game_invitation": 5,
    "choose_move": 30,
    "match_result": 10,
    "default": 10
  },
  
  "retry_policy": {
    "max_retries": 3,
    "base_delay_seconds": 2,
    "backoff_multiplier": 1.0,
    "retryable_errors": ["E001", "E009"]
  },
  
  "capacity_limits": {
    "max_players": 50,
    "max_referees": 10,
    "max_concurrent_matches": 10,
    "max_leagues": 5
  }
}
```

**Validation Rules:**
- ✅ `schema_version` must be present and valid semver format
- ✅ `protocol_version` must match supported range (2.0.0 - 2.1.0)
- ✅ Port ranges must not overlap
- ✅ Timeout values must be positive integers
- ✅ Timestamp must be ISO8601 UTC format

### 3.4 Schema: leagues/league_{id}.json

**Purpose**: Define league-specific configuration.

```json
{
  "id": "league_even_odd_2025",
  "schema_version": "1.0.0",
  "last_updated": "2025-01-15T10:00:00Z",
  
  "league_meta": {
    "display_name": "Even/Odd Championship 2025",
    "game_type": "even_odd",
    "season": "2025-spring",
    "status": "scheduled",
    "scheduled_start": "2025-01-20T14:00:00Z",
    "scheduled_end": "2025-01-20T18:00:00Z"
  },
  
  "rules": {
    "tournament_format": "round_robin",
    "match_type": "head_to_head",
    "scoring": {
      "win": 3,
      "tie": 1,
      "loss": 0,
      "technical_loss": 0
    },
    "tiebreaker_order": [
      "total_points",
      "head_to_head",
      "win_percentage",
      "player_id_alphabetical"
    ]
  },
  
  "constraints": {
    "min_players": 2,
    "max_players": 50,
    "registration_deadline": "2025-01-20T13:00:00Z",
    "allow_late_registration": false
  }
}
```

**Validation Rules:**
- ✅ `game_type` must exist in games/registry.json
- ✅ `scheduled_start` must be after `last_updated`
- ✅ `registration_deadline` must be before `scheduled_start`
- ✅ Scoring values must be non-negative integers
- ✅ `status`: scheduled | registration_open | in_progress | completed | cancelled

### 3.5 Configuration Best Practices

**DO:**
- ✅ Version all configuration files (schema_version)
- ✅ Validate configuration at startup (fail fast)
- ✅ Provide default fallbacks for optional settings
- ✅ Use environment variables for secrets (not in config files)

**DON'T:**
- ❌ Store secrets or credentials in config files
- ❌ Modify config files during runtime
- ❌ Use relative paths (always absolute paths)
- ❌ Store runtime data in config/ directory


---

## 4. Layer 2: Runtime Data Layer (data/)

### 4.1 Overview

**Purpose**: Store dynamic game state, historical records, and player progress.

**Philosophy**: This is the "memory" - it records what *has happened* and what *is happening now*.

**Access Pattern**: Read and write frequently during tournament operation.

### 4.2 Directory Structure

```
data/
├── leagues/                       # League-specific data
│   └── {league_id}/
│       ├── standings.json         # Current standings
│       ├── schedule.json          # Match schedule
│       ├── rounds.json            # Round-by-round data
│       └── players.json           # Registered players
│
├── matches/                       # Match-level data
│   └── {league_id}/
│       └── {round_id}/
│           ├── R1M1.json          # Individual match data
│           ├── R1M2.json
│           └── round_summary.json
│
├── players/                       # Player-specific data
│   └── {player_id}/
│       ├── profile.json           # Player metadata
│       ├── match_history.json    # All matches
│       └── opponent_profiles.json # Learned opponent patterns
│
├── referees/                      # Referee-specific data
│   └── {referee_id}/
│       ├── profile.json
│       └── match_assignments.json
│
└── backups/                       # Automated backups
    └── {timestamp}/
        └── {league_id}/
            └── standings.json
```

### 4.3 Schema: data/leagues/{league_id}/standings.json

**Purpose**: Current tournament standings (updated after each match).

```json
{
  "id": "standings_league_even_odd_2025",
  "schema_version": "1.0.0",
  "last_updated": "2025-01-20T14:35:22Z",
  "league_id": "league_even_odd_2025",
  "round_id": 2,
  
  "standings": [
    {
      "rank": 1,
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "games_played": 3,
      "wins": 2,
      "losses": 0,
      "ties": 1,
      "points": 7,
      "win_rate": 0.667,
      "avg_response_time_ms": 1250,
      "technical_losses": 0,
      "status": "ACTIVE"
    }
  ],
  
  "statistics": {
    "total_players": 10,
    "total_matches_completed": 15,
    "total_matches_scheduled": 45,
    "completion_percentage": 33.3
  }
}
```

**Update Frequency**: After every match result

**Validation Rules:**
- ✅ Points calculation: wins×3 + ties×1
- ✅ Rank must be sequential starting from 1
- ✅ win_rate = wins / games_played (or 0 if no games)
- ✅ games_played = wins + losses + ties
- ✅ All player_ids must be unique

**Performance Requirements:**
- Update latency < 5 seconds after match result
- Query response time < 1 second for 50 players
- Concurrent read access supported

### 4.4 Schema: data/matches/{league_id}/{round_id}/{match_id}.json

**Purpose**: Complete match record including all moves and outcome.

```json
{
  "id": "R1M1",
  "schema_version": "1.0.0",
  "last_updated": "2025-01-20T14:05:45Z",
  "league_id": "league_even_odd_2025",
  "round_id": 1,
  "match_id": "R1M1",
  
  "match_meta": {
    "game_type": "even_odd",
    "referee_id": "REF01",
    "conversation_id": "convr1m1001",
    "start_time": "2025-01-20T14:00:03Z",
    "end_time": "2025-01-20T14:05:45Z",
    "duration_seconds": 342
  },
  
  "players": {
    "player_A": {
      "player_id": "P01",
      "display_name": "Agent Alpha",
      "role": "player1"
    },
    "player_B": {
      "player_id": "P02",
      "display_name": "Agent Beta",
      "role": "player2"
    }
  },
  
  "result": {
    "status": "COMPLETED",
    "winner_id": "P01",
    "result_type": "WIN",
    "choices": {
      "P01": "odd",
      "P02": "even"
    },
    "drawn_number": 7,
    "parity": "odd",
    "points_awarded": {
      "P01": 3,
      "P02": 0
    }
  },
  
  "performance_metrics": {
    "P01": {
      "invitation_response_time_ms": 1200,
      "move_response_time_ms": 1500
    },
    "P02": {
      "invitation_response_time_ms": 2100,
      "move_response_time_ms": 2800
    }
  }
}
```

**Validation Rules:**
- ✅ Winner must be one of the players (or null for tie)
- ✅ Points must sum correctly based on result
- ✅ All player_ids must be registered

### 4.5 Schema: data/players/{player_id}/match_history.json

**Purpose**: Player's complete match history for strategy learning.

```json
{
  "id": "match_history_P01",
  "schema_version": "1.0.0",
  "last_updated": "2025-01-20T14:35:22Z",
  "player_id": "P01",
  
  "summary": {
    "total_matches": 15,
    "wins": 10,
    "losses": 3,
    "ties": 2,
    "win_rate": 0.667,
    "total_points": 32
  },
  
  "matches": [
    {
      "match_id": "R1M1",
      "timestamp": "2025-01-20T14:05:45Z",
      "opponent_id": "P02",
      "my_choice": "odd",
      "opponent_choice": "even",
      "drawn_number": 7,
      "result": "WIN",
      "points": 3
    }
  ],
  
  "opponent_statistics": {
    "P02": {
      "matches_played": 1,
      "wins_vs": 1,
      "losses_vs": 0,
      "ties_vs": 0
    }
  }
}
```

**Update Frequency**: After every match completion

**Storage Limits**: Keep last 1000 matches (configurable)

### 4.6 Runtime Data Best Practices

**DO:**
- ✅ Version all data files (schema_version)
- ✅ Timestamp all updates (last_updated)
- ✅ Use atomic file writes (write to temp, then rename)
- ✅ Implement backup strategy (before major updates)
- ✅ Validate data integrity on read
- ✅ Use file locking for concurrent writes

**DON'T:**
- ❌ Store derived data (compute on demand)
- ❌ Use relative timestamps (always absolute UTC)
- ❌ Allow unbounded growth (implement retention policies)
- ❌ Skip validation (corrupt data causes cascading failures)


---

## 5. Layer 3: Logs Layer (logs/)

### 5.1 Overview

**Purpose**: Track all system events for debugging, auditing, and monitoring.

**Philosophy**: This is the "nervous system" - it provides sensory feedback about what's happening in the system.

**Access Pattern**: Append-only writes during runtime, read for debugging and analysis.

### 5.2 Directory Structure

```
logs/
├── league/                        # League Manager logs
│   └── {league_id}/
│       └── league_YYYYMMDD.jsonl  # Daily log rotation
│
├── referees/                      # Referee logs
│   └── {referee_id}/
│       └── referee_YYYYMMDD.jsonl
│
├── players/                       # Player agent logs
│   └── {player_id}/
│       └── player_YYYYMMDD.jsonl
│
├── matches/                       # Match-specific logs
│   └── {league_id}/
│       └── {match_id}.jsonl       # All events for one match
│
└── system/                        # System-wide logs
    ├── errors.jsonl               # All errors across system
    ├── security.jsonl             # Auth failures, suspicious activity
    └── performance.jsonl          # Performance metrics
```

### 5.3 Log Format: JSON Lines (JSONL)

**Why JSON Lines?**
- ✅ Each line is a valid JSON object (easy to parse)
- ✅ Append-only (no need to parse entire file)
- ✅ Streamable (can process while writing)
- ✅ Grep-able (can search with standard tools)
- ✅ Tools support: jq, logstash, fluentd

**Example: logs/league/{league_id}/league_20250120.jsonl**

```jsonl
{"timestamp":"2025-01-20T14:00:00Z","level":"INFO","component":"league_manager","message":"Tournament started","league_id":"league_even_odd_2025","total_players":10}
{"timestamp":"2025-01-20T14:00:01Z","level":"INFO","component":"league_manager","message":"Round 1 announced","league_id":"league_even_odd_2025","round_id":1,"matches":5}
{"timestamp":"2025-01-20T14:05:45Z","level":"INFO","component":"league_manager","message":"Match result received","league_id":"league_even_odd_2025","match_id":"R1M1","winner":"P01"}
```

### 5.4 Schema: Standard Log Entry

**Required Fields (All Logs):**

```json
{
  "timestamp": "2025-01-20T14:00:00.123456Z",
  "level": "INFO",
  "component": "league_manager",
  "message": "Human-readable message"
}
```

**Optional Context Fields:**

```json
{
  "league_id": "league_even_odd_2025",
  "round_id": 1,
  "match_id": "R1M1",
  "player_id": "P01",
  "referee_id": "REF01",
  "conversation_id": "convr1m1001",
  "error_code": "E001",
  "duration_ms": 1250,
  "data": {
    "custom_field": "value"
  }
}
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: Normal operational events
- `WARN`: Warning events (potential issues)
- `ERROR`: Error events (operation failed)
- `CRITICAL`: Critical failures (system instability)

### 5.5 Schema: Match Log (logs/matches/{league_id}/{match_id}.jsonl)

**Purpose**: Complete chronological log of all events in one match.

```jsonl
{"timestamp":"2025-01-20T14:00:03Z","level":"INFO","component":"referee","conversation_id":"convr1m1001","message":"Match started","match_id":"R1M1","player_A":"P01","player_B":"P02"}
{"timestamp":"2025-01-20T14:00:04.200Z","level":"INFO","component":"referee","conversation_id":"convr1m1001","message":"Invitation accepted","match_id":"R1M1","player_id":"P01","response_time_ms":1200}
{"timestamp":"2025-01-20T14:00:08.500Z","level":"INFO","component":"referee","conversation_id":"convr1m1001","message":"Move received","match_id":"R1M1","player_id":"P01","choice":"odd","response_time_ms":1500}
{"timestamp":"2025-01-20T14:00:10Z","level":"INFO","component":"referee","conversation_id":"convr1m1001","message":"Number drawn","match_id":"R1M1","drawn_number":7,"parity":"odd"}
{"timestamp":"2025-01-20T14:00:11Z","level":"INFO","component":"referee","conversation_id":"convr1m1001","message":"Winner determined","match_id":"R1M1","winner":"P01"}
```

### 5.6 Schema: Error Log (logs/system/errors.jsonl)

**Purpose**: Centralized error tracking across all components.

```jsonl
{"timestamp":"2025-01-20T14:10:30Z","level":"ERROR","component":"referee","message":"Player timeout","error_code":"E001","error_name":"TIMEOUT_ERROR","match_id":"R2M3","player_id":"P05","retry_count":1,"max_retries":3}
{"timestamp":"2025-01-20T14:10:34Z","level":"ERROR","component":"referee","message":"Player timeout (final)","error_code":"E001","match_id":"R2M3","player_id":"P05","retry_count":3,"result":"TECHNICAL_LOSS"}
```

**Query Examples:**
```bash
# Find all E001 timeout errors
grep 'E001' logs/system/errors.jsonl

# Find all errors for player P05
grep 'P05' logs/system/errors.jsonl | jq -r '{timestamp, error_code, message}'

# Count errors by error_code
jq -r .error_code logs/system/errors.jsonl | sort | uniq -c
```

### 5.7 Log Retention Policy

**Retention Periods:**
- **Match logs**: 90 days (critical for disputes)
- **System errors**: 365 days (trend analysis)
- **Performance logs**: 30 days (recent optimization)
- **DEBUG level logs**: 7 days (disk space management)
- **INFO/WARN/ERROR logs**: 90 days (operational history)

**Rotation Strategy:**
- Daily rotation (new file per day)
- Compress files older than 7 days (gzip)
- Archive to cold storage after retention period

**Example Rotation:**
```
logs/league/league_even_odd_2025/
├── league_20250120.jsonl           # Today (active)
├── league_20250119.jsonl           # Yesterday
├── league_20250118.jsonl.gz        # Compressed
└── league_20250117.jsonl.gz
```

### 5.8 Logs Layer Best Practices

**DO:**
- ✅ Use structured JSON logs (not plain text)
- ✅ Include conversation_id for match-related logs
- ✅ Log at appropriate levels (don't over-log DEBUG)
- ✅ Include timestamp with microsecond precision
- ✅ Redact sensitive data (auth tokens, passwords)
- ✅ Use UTC timestamps exclusively
- ✅ Implement log rotation (prevent disk fill)

**DON'T:**
- ❌ Log PII unnecessarily
- ❌ Log secrets or credentials
- ❌ Use logs for data storage (use data/ layer)
- ❌ Skip context fields (harder to debug)
- ❌ Use ambiguous messages ("Error occurred")


---

## 6. Cross-Layer Patterns

### 6.1 Data Flow Between Layers

```
STARTUP FLOW:
1. config/ → Load system configuration (read-only)
2. config/ → Load league configuration
3. data/ → Initialize runtime data structures
4. logs/ → Initialize log files

MATCH EXECUTION FLOW:
1. config/ → Read timeout settings
2. data/ → Load player profiles and standings
3. Match executes (in memory)
4. logs/ → Log all match events
5. data/ → Update match result
6. data/ → Update standings
7. logs/ → Log standings update

SHUTDOWN FLOW:
1. data/ → Flush pending writes
2. data/ → Create backup snapshot
3. logs/ → Log shutdown event
4. logs/ → Flush and close log files
```

### 6.2 Unique Identifiers Across Layers

**ID Formats:**

| Entity | ID Format | Example | Usage |
|--------|-----------|---------|-------|
| League | `league_{game}_{year}` | `league_even_odd_2025` | config, data, logs |
| Round | `{round_number}` | `1`, `2`, `3` | data, logs |
| Match | `R{round}M{match_num}` | `R1M1`, `R2M5` | data, logs |
| Player | `P{sequential}` | `P01`, `P02` | config, data, logs |
| Referee | `REF{sequential}` | `REF01`, `REF02` | config, data, logs |
| Conversation | `convr{round}m{match}{random}` | `convr1m1001` | logs |

**Consistency Rule**: IDs must be globally unique within scope.

### 6.3 Schema Versioning Strategy

**Version Format**: Semantic Versioning (MAJOR.MINOR.PATCH)

**Version Bump Rules:**
- **MAJOR**: Breaking changes (incompatible schema)
- **MINOR**: Backward-compatible additions (new optional fields)
- **PATCH**: Bug fixes, documentation updates

**Example Evolution:**
```json
// Version 1.0.0 (Initial)
{
  "schema_version": "1.0.0",
  "player_id": "P01",
  "wins": 10,
  "losses": 5
}

// Version 1.1.0 (Add optional field - MINOR bump)
{
  "schema_version": "1.1.0",
  "player_id": "P01",
  "wins": 10,
  "losses": 5,
  "ties": 2  // NEW FIELD (optional)
}

// Version 2.0.0 (Breaking change - MAJOR bump)
{
  "schema_version": "2.0.0",
  "player_id": "P01",
  "record": {  // BREAKING: Restructured
    "wins": 10,
    "losses": 5,
    "ties": 2
  }
}
```

---

## 7. Data Management Best Practices

### 7.1 File Naming Conventions

**Configuration Files:**
- Format: `{entity_type}_{identifier}.json`
- Examples: `league_even_odd_2025.json`, `system.json`
- Case: lowercase with underscores

**Data Files:**
- Format: `{entity_type}.json` or `{identifier}.json`
- Examples: `standings.json`, `R1M1.json`
- Case: lowercase for types, uppercase for match IDs

**Log Files:**
- Format: `{component}_{YYYYMMDD}.jsonl`
- Examples: `league_20250120.jsonl`, `referee_20250120.jsonl`
- Case: lowercase with date suffix

### 7.2 Atomic File Operations

**Problem**: Concurrent writes or crashes can corrupt files.

**Solution**: Atomic write pattern

```python
import json
import os
from pathlib import Path

def atomic_write(filepath: str, data: dict):
    """
    Write JSON data atomically to prevent corruption.
    """
    filepath = Path(filepath)
    temp_filepath = filepath.with_suffix('.tmp')
    
    # Write to temporary file
    with open(temp_filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Atomic rename
    os.replace(temp_filepath, filepath)
```

**Benefits:**
- ✅ Prevents partial writes
- ✅ Prevents corruption on crash
- ✅ Ensures file is always in valid state

### 7.3 Backup Strategy

**Backup Schedule:**
- **Before major updates**: standings, schedule
- **After each round**: complete league state
- **Daily**: all data/ directory
- **Before tournament**: complete system snapshot

**Backup Implementation:**
```python
from datetime import datetime
import shutil
from pathlib import Path

def create_backup(source_dir: str, backup_root: str):
    """Create timestamped backup of directory."""
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    backup_dir = Path(backup_root) / timestamp
    
    shutil.copytree(source_dir, backup_dir)
    return str(backup_dir)
```

**Backup Retention:**
- Keep last 10 backups
- Keep daily backups for 30 days
- Archive monthly backups indefinitely

### 7.4 Data Validation

**Validation Levels:**

**1. Schema Validation (Structure)**
```python
from jsonschema import validate

standings_schema = {
    "type": "object",
    "required": ["id", "schema_version", "league_id", "standings"],
    "properties": {
        "schema_version": {"type": "string"},
        "league_id": {"type": "string"},
        "standings": {
            "type": "array",
            "items": {
                "required": ["rank", "player_id", "points"]
            }
        }
    }
}

validate(instance=data, schema=standings_schema)
```

**2. Business Logic Validation**
```python
def validate_standings_logic(data):
    """Validate business rules."""
    errors = []
    
    # Check ranks are sequential
    ranks = [p['rank'] for p in data['standings']]
    expected = list(range(1, len(ranks) + 1))
    if ranks != expected:
        errors.append("Ranks must be sequential")
    
    # Check points calculation
    for player in data['standings']:
        expected_points = player['wins'] * 3 + player['ties'] * 1
        if player['points'] != expected_points:
            errors.append(f"Invalid points for {player['player_id']}")
    
    return len(errors) == 0, errors
```


---

## 8. Integration Points

### 8.1 League Manager Integration

**Reads From:**
- config/system.json - System settings
- config/leagues/{league_id}.json - League configuration
- config/defaults/timeouts.json - Timeout settings
- data/leagues/{league_id}/players.json - Registered players
- data/leagues/{league_id}/standings.json - Current standings

**Writes To:**
- data/leagues/{league_id}/standings.json - After each match
- data/leagues/{league_id}/schedule.json - Tournament schedule
- logs/league/{league_id}/league_{date}.jsonl - Operational logs
- logs/system/errors.jsonl - Error events

### 8.2 Referee Integration

**Reads From:**
- config/system.json - Timeout settings
- config/games/{game_type}.json - Game rules
- data/leagues/{league_id}/schedule.json - Match assignments

**Writes To:**
- data/matches/{league_id}/{round_id}/{match_id}.json - Match result
- logs/referees/{referee_id}/referee_{date}.jsonl - Referee logs
- logs/matches/{league_id}/{match_id}.jsonl - Match event log
- logs/system/errors.jsonl - Error events

### 8.3 Player Agent Integration

**Reads From:**
- data/players/{player_id}/match_history.json - Past matches
- data/players/{player_id}/opponent_profiles.json - Opponent patterns
- data/leagues/{league_id}/standings.json - Current standings

**Writes To:**
- data/players/{player_id}/match_history.json - After each match
- data/players/{player_id}/opponent_profiles.json - After learning
- logs/players/{player_id}/player_{date}.jsonl - Agent logs

---

## 9. User Stories

### 9.1 Configuration Layer

**US-1: System Configuration**
> As a system administrator  
> I want to centralize all system settings in config/system.json  
> So that I can configure the entire system from one file  
>
> Acceptance Criteria:
> - All timeout values read from config/defaults/timeouts.json
> - Port allocation read from config/system.json
> - Configuration validated at startup
> - Invalid configuration causes fail-fast with clear error

**US-2: League Configuration**
> As a tournament organizer  
> I want to define league rules in config/leagues/{league_id}.json  
> So that the system enforces my custom rules automatically  
>
> Acceptance Criteria:
> - Scoring rules applied correctly (Win=3, Tie=1)
> - Registration deadline enforced
> - Tiebreaker logic follows configuration order

### 9.2 Runtime Data Layer

**US-3: Standings Tracking**
> As a player  
> I want to query current standings from data/leagues/{league_id}/standings.json  
> So that I know my current rank and adjust strategy  
>
> Acceptance Criteria:
> - Standings updated within 5 seconds of match completion
> - Rankings calculated correctly with tiebreakers
> - Historical standings preserved for each round

**US-4: Match History**
> As a player agent  
> I want to access my match history from data/players/{player_id}/match_history.json  
> So that I can implement learning algorithms  
>
> Acceptance Criteria:
> - All matches recorded with full details
> - Opponent statistics aggregated
> - Last 1000 matches retained

### 9.3 Logs Layer

**US-5: Match Debugging**
> As a developer  
> I want to see all events for a match in logs/matches/{league_id}/{match_id}.jsonl  
> So that I can debug match-specific failures  
>
> Acceptance Criteria:
> - All events logged in chronological order
> - conversation_id consistent across all events
> - Response times recorded for performance analysis

**US-6: Error Aggregation**
> As a system administrator  
> I want to see all errors in logs/system/errors.jsonl  
> So that I can identify systemic issues  
>
> Acceptance Criteria:
> - All errors from all components aggregated
> - Error codes included for programmatic analysis
> - Context fields enable root cause analysis

---

## 10. Acceptance Criteria

### 10.1 Configuration Layer
- All config files have id, schema_version, last_updated
- Configuration validated at startup (fail fast on errors)
- Default values provided for optional settings
- Environment variables override config for secrets
- Configuration changes require system restart

### 10.2 Runtime Data Layer
- All data files have id, schema_version, last_updated
- Atomic file writes prevent corruption
- Backups created before major updates
- Schema validation on all reads and writes
- Referential integrity maintained (IDs are valid)
- Data retention policies enforced

### 10.3 Logs Layer
- All logs in JSON Lines format
- Timestamp in UTC with microsecond precision
- conversation_id included for match-related logs
- Log levels used appropriately
- Sensitive data redacted
- Daily log rotation implemented
- Compression after 7 days
- Retention policies enforced

### 10.4 Cross-Layer
- Unique IDs consistent across all layers
- Schema versioning enables migrations
- Data flow follows defined patterns
- Integration points well-defined
- Error handling at all I/O boundaries

---

## 11. Success Metrics

### 11.1 Functional Metrics
- Configuration Compliance: 100% of files have required fields
- Data Integrity: 0% corruption rate (atomic writes working)
- Schema Validation: 100% of data files validated on read
- Backup Success Rate: 100% of backups complete successfully
- Log Completeness: 100% of critical events logged

### 11.2 Performance Metrics
- Standings Update Latency: < 5 seconds
- Match Data Write Time: < 1 second
- Config Load Time: < 2 seconds at startup
- Log Write Latency: < 10ms (async writes)
- Data Query Time: < 500ms for standings (50 players)

### 11.3 Operational Metrics
- Disk Space Usage: < 1GB for 100-player, 10-round tournament
- Log Retention Compliance: 100% (automated rotation working)
- Backup Retention: Last 10 backups + 30 days daily
- Schema Migration Success: 100% of files migrated without data loss

---

## Appendix: Implementation Checklist

**Configuration Layer Setup:**
- [ ] Create config/ directory structure
- [ ] Define system.json with all required fields
- [ ] Create league configuration templates
- [ ] Implement configuration validation
- [ ] Add environment variable support for secrets

**Runtime Data Layer Setup:**
- [ ] Create data/ directory structure
- [ ] Implement atomic write functions
- [ ] Set up backup automation
- [ ] Create data validation schemas
- [ ] Implement retention policies

**Logs Layer Setup:**
- [ ] Create logs/ directory structure
- [ ] Implement structured logging (JSON Lines)
- [ ] Set up log rotation (daily)
- [ ] Implement log compression (gzip after 7 days)
- [ ] Create log query tools

**Cross-Layer Integration:**
- [ ] Define and enforce ID formats
- [ ] Implement schema migration tool
- [ ] Create backup/restore scripts
- [ ] Set up integration tests
- [ ] Document data flow patterns

---

**Document Status:** FINAL  
**Last Updated:** 2025-12-20  
**Approvers:** Technical Lead, System Architect, DevOps Lead

