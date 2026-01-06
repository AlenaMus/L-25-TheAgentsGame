# Architecture Index

**Document Type:** Navigation Guide
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL

---

## Purpose

This document provides an index to all architecture documentation for the Even/Odd Game League system. Use this as your starting point to navigate the modular architecture documents.

---

## Architecture Document Organization

The architecture is organized into **three categories**:

### 1. Common Design Patterns (Foundation)
Documents that apply to ALL agents (League Manager, Referees, Players)

### 2. Agent-Specific Architectures
Complete implementation templates for each agent type

### 3. Infrastructure Layer Architectures
Cross-cutting concerns (configuration, data, logging)

---

## Common Design Patterns (Foundation)

### ✅ [common-design.md](./common-design.md)
**Status:** Complete | **Lines:** 800+ | **Priority:** CRITICAL

**What it covers:**
- MCP Server Pattern (FastAPI template)
- JSON-RPC 2.0 Communication
- Tool Registration Pattern
- Error Handling Hierarchy
- Retry Logic with Exponential Backoff
- Circuit Breaker Pattern
- Structured Logging
- Timeout Management

**When to use:** Read this FIRST before implementing any agent.

---

### ✅ [message-envelope-design.md](./message-envelope-design.md)
**Status:** Complete | **Lines:** 500+ | **Priority:** CRITICAL

**What it covers:**
- Standard message envelope structure
- Required fields (protocol, message_type, sender, timestamp, conversation_id)
- Optional fields (auth_token, league_id, round_id, match_id)
- UTC timezone enforcement
- Validation rules and Pydantic schemas

**When to use:** When implementing any message sender or receiver.

---

### ✅ [authentication-design.md](./authentication-design.md)
**Status:** Complete | **Lines:** 600+ | **Priority:** CRITICAL

**What it covers:**
- Token lifecycle (generation → storage → usage → expiry)
- Secure token generation (secrets module)
- Token validation patterns
- Error handling (E011, E012, E013)
- Security best practices

**When to use:** When implementing registration or authenticated requests.

---

### ✅ [state-management-design.md](./state-management-design.md)
**Status:** Complete | **Lines:** 400+ | **Priority:** CRITICAL

**What it covers:**
- Game state machine (WAITING_FOR_PLAYERS → ... → FINISHED)
- Round state management
- Player state persistence
- State transition rules
- Recovery patterns

**When to use:** When implementing game flow or round management.

---

### ⏳ [data-persistence-design.md](./data-persistence-design.md)
**Status:** In Progress | **Priority:** CRITICAL

**What it will cover:**
- Atomic file writes (write-to-temp then rename)
- Backup strategies
- Schema versioning
- File organization (config/, data/, logs/)
- JSON serialization patterns
- Corruption prevention

**When to use:** When implementing any file I/O operations.

---

## Agent-Specific Architectures

### ✅ [league-manager-architecture.md](./league-manager-architecture.md)
**Status:** Complete | **Lines:** 700+ | **Priority:** HIGH

**What it covers:**
- Registration handlers (referee + player)
- Round-robin scheduling algorithm
- Standings calculation with tiebreakers
- Round management (announcement → completion)
- Broadcast patterns (to all players/referees)
- Complete implementation template

**When to use:** When implementing the League Manager agent.

---

### ✅ [referee-architecture.md](./referee-architecture.md)
**Status:** Complete | **Lines:** 800+ | **Priority:** HIGH

**What it covers:**
- Game orchestration (6-phase flow)
- Simultaneous move collection pattern
- Winner determination (cryptographic random 1-10)
- Timeout enforcement with retry
- Result reporting to League Manager
- Complete implementation template

**When to use:** When implementing a Referee agent.

---

### ✅ [player-agent-architecture.md](./player-agent-architecture.md)
**Status:** Complete | **Lines:** 900+ | **Priority:** HIGH

**What it covers:**
- 3 Required MCP tools (handle_game_invitation, choose_parity, notify_match_result)
- Strategy interface and implementations (Random, Adaptive, LLM)
- Pattern detection algorithms (frequency analysis, chi-squared test)
- Game history storage and querying
- Complete implementation template

**When to use:** When implementing a Player Agent (YOUR MAIN TASK).

---

### ✅ [game-flow-design.md](./game-flow-design.md)
**Status:** Complete | **Lines:** 1000+ | **Priority:** CRITICAL

**What it covers:**
- Complete tournament flow (6 phases: Registration → Scheduling → Round Announcement → Match Orchestration → Round Completion → League Completion)
- Message sequences for each phase
- State transitions and dependencies
- Timeout handling and error recovery
- Complete end-to-end flow diagrams

**When to use:** When understanding the complete system flow or implementing any orchestration logic.

---

### ✅ [player-strategy-design.md](./player-strategy-design.md)
**Status:** Complete | **Lines:** 1000+ | **Priority:** HIGH

**What it covers:**
- Strategy interface design
- Random Strategy (baseline)
- Adaptive Strategy (pattern detection with chi-squared test, frequency analysis, streak detection)
- LLM-Enhanced Strategy (optional)
- Markov Chain analysis
- Statistical pattern detection algorithms
- Performance comparison and benchmarking

**When to use:** When implementing player decision logic and strategy algorithms.

---

## Infrastructure Layer Architectures

### ⏳ [configuration-layer-architecture.md](./configuration-layer-architecture.md)
**Status:** Pending | **Priority:** MEDIUM

**What it will cover:**
- File structure (system.json, leagues/, games/, defaults/)
- Schema specifications
- Validation rules
- Environment variable overrides
- Loading and caching patterns

**When to use:** When implementing configuration loading.

---

### ⏳ [logging-layer-architecture.md](./logging-layer-architecture.md)
**Status:** Pending | **Priority:** MEDIUM

**What it will cover:**
- JSON Lines format specification
- Required fields (timestamp, level, agent_id, message)
- Log levels (DEBUG, INFO, WARN, ERROR, CRITICAL)
- Log rotation and retention
- Query patterns (grep, jq)
- Centralized aggregation

**When to use:** When implementing logging infrastructure.

---

### ✅ [three-layer-architecture-requirements.md](./three-layer-architecture-requirements.md)
**Status:** Complete | **Lines:** 1100+ | **Priority:** MEDIUM

**What it covers:**
- Complete three-layer file system architecture
- Configuration layer (config/)
- Runtime data layer (data/)
- Logs layer (logs/)
- Data management patterns
- Integration points between layers

**When to use:** When organizing the file system or implementing file I/O.

---

## Quick Reference by Task

### "I want to implement a Player Agent"
**Read in this order:**
1. [common-design.md](./common-design.md) - Base MCP server pattern
2. [message-envelope-design.md](./message-envelope-design.md) - Message structure
3. [authentication-design.md](./authentication-design.md) - Registration and auth
4. [game-flow-design.md](./game-flow-design.md) - Complete tournament flow
5. [player-agent-architecture.md](./player-agent-architecture.md) - Player-specific implementation
6. [player-strategy-design.md](./player-strategy-design.md) - Strategy algorithms
7. [state-management-design.md](./state-management-design.md) - Game state tracking

### "I want to implement a Referee"
**Read in this order:**
1. [common-design.md](./common-design.md) - Base MCP server pattern
2. [message-envelope-design.md](./message-envelope-design.md) - Message structure
3. [authentication-design.md](./authentication-design.md) - Registration and auth
4. [game-flow-design.md](./game-flow-design.md) - Complete tournament flow
5. [referee-architecture.md](./referee-architecture.md) - Referee-specific implementation
6. [state-management-design.md](./state-management-design.md) - Game state machine

### "I want to implement League Manager"
**Read in this order:**
1. [common-design.md](./common-design.md) - Base MCP server pattern
2. [message-envelope-design.md](./message-envelope-design.md) - Message structure
3. [authentication-design.md](./authentication-design.md) - Token generation
4. [game-flow-design.md](./game-flow-design.md) - Complete tournament flow
5. [league-manager-architecture.md](./league-manager-architecture.md) - League Manager implementation
6. [data-persistence-design.md](./data-persistence-design.md) - Standings persistence

### "I want to understand the file system"
**Read in this order:**
1. [three-layer-architecture-requirements.md](./three-layer-architecture-requirements.md) - Complete file structure
2. [configuration-layer-architecture.md](./configuration-layer-architecture.md) - Config files
3. [data-persistence-design.md](./data-persistence-design.md) - Data files
4. [logging-layer-architecture.md](./logging-layer-architecture.md) - Log files

### "I want to understand message flow"
**Read in this order:**
1. [message-envelope-design.md](./message-envelope-design.md) - Message structure
2. [common-design.md](./common-design.md) - JSON-RPC communication
3. [game-protocol-messages-prd.md](../requirements/game-protocol-messages-prd.md) - All 18 message types

---

## Implementation Roadmap

### Phase 1: Foundation (COMPLETE ✅)
- [x] common-design.md
- [x] message-envelope-design.md
- [x] authentication-design.md
- [x] state-management-design.md
- [x] three-layer-architecture-requirements.md
- [ ] data-persistence-design.md (optional - covered in three-layer doc)

### Phase 2: Agent Architectures (COMPLETE ✅)
- [x] player-agent-architecture.md
- [x] referee-architecture.md
- [x] league-manager-architecture.md
- [x] game-flow-design.md
- [x] player-strategy-design.md

### Phase 3: Infrastructure (Optional)
- [ ] configuration-layer-architecture.md (optional - covered in three-layer doc)
- [ ] logging-layer-architecture.md (optional - covered in implementation standards)

---

## Document Standards

All architecture documents follow these standards:

### Structure
- Table of Contents
- Introduction (purpose, scope)
- Design sections with examples
- Implementation code snippets (Python)
- Summary
- Related documents links

### Code Examples
- Runnable Python code (Python 3.11+)
- Type hints on all functions
- Comments explaining key decisions
- Error handling included

### Diagrams
- ASCII art for flow diagrams
- State machines as labeled graphs
- Sequence diagrams for message flows

---

## References

### Requirements Documents
- [league-system-prd.md](../requirements/league-system-prd.md) - League Manager requirements
- [even-odd-game-prd.md](../requirements/even-odd-game-prd.md) - Game rules and mechanics
- [game-protocol-messages-prd.md](../requirements/game-protocol-messages-prd.md) - All 18 message types
- [implementation-architecture-prd.md](../requirements/implementation-architecture-prd.md) - Implementation patterns
- [developer-implementation-guide.md](../requirements/developer-implementation-guide.md) - Quick start guide
- [project-folder-structure-guide.md](../requirements/project-folder-structure-guide.md) - Folder organization

### Operational Guides
- [game-orchestrator-runtime-guide.md](../guides/game-orchestrator-runtime-guide.md) - Running the complete system

---

## Contributing

When creating new architecture documents:

1. **Follow the template** from existing documents
2. **Include code examples** for all patterns
3. **Cross-reference** related documents
4. **Keep focused** - one document per concept
5. **Implementation-ready** - developers should be able to code directly from the doc

---

## Status Legend

- ✅ **Complete** - Document finished and reviewed
- ⏳ **In Progress** - Currently being written
- ⏸️ **Pending** - Planned but not started
- ❌ **Deprecated** - No longer relevant

---

## Summary

This architecture is designed for **autonomous implementation**:
- Each document is self-contained
- Clear interfaces between components
- No circular dependencies
- Complete code examples

**Next Steps:**
1. Read common-design.md for foundational patterns
2. Choose your agent type (Player, Referee, or League Manager)
3. Follow the "Quick Reference by Task" guide above
4. Implement using the patterns and templates provided

---

**Document Status:** FINAL
**Last Updated:** 2025-12-20
**Version:** 1.0
**Maintainer:** Architecture Team
