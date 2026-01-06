# Game Orchestrator Architecture Design

**Document Type:** Architecture Design
**Version:** 1.0
**Last Updated:** 2025-12-24
**Status:** FINAL
**Target Audience:** Backend Developers, System Architects

---

## Executive Summary

The **Game Orchestrator** is a master controller application that manages the complete Even/Odd tournament system lifecycle. It acts as the operational nerve center, coordinating startup, monitoring health, managing tournament flow, and providing real-time observability across all agents (League Manager, Referees, and Players).

### Key Strengths
- Centralized lifecycle management for all 7+ agents
- Real-time monitoring with WebSocket dashboard
- Automated startup sequence enforcement
- Health monitoring with automatic recovery
- Comprehensive error handling and logging aggregation

### Critical Requirements Addressed
- Enforces critical startup order (League Manager → Referees → Players)
- Monitors 7-stage tournament flow from registration to completion
- Handles agent crashes with automatic restart capabilities
- Provides real-time observability through web dashboard
- Aggregates logs from all agents for centralized debugging

---

## Architecture Overview

### System Context

```
┌────────────────────────────────────────────────────────────────┐
│                    GAME ORCHESTRATOR                            │
│                  (Master Controller)                            │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Lifecycle Mgr  │  │ Health Monitor │  │ Dashboard Server│  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
│  ┌────────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │Tournament Ctrl │  │ Error Recovery │  │ Log Aggregator  │  │
│  └────────────────┘  └────────────────┘  └─────────────────┘  │
└────────────────────────────────────────────────────────────────┘
                            ↕ HTTP/JSON-RPC
┌────────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                                │
│                                                                  │
│  ┌──────────────┐                                               │
│  │League Manager│ (Port 8000)                                   │
│  └──────────────┘                                               │
│         ↕                                                        │
│  ┌──────────┐  ┌──────────┐                                    │
│  │Referee 01│  │Referee 02│ (Ports 8001-8010)                  │
│  └──────────┘  └──────────┘                                    │
│         ↕              ↕                                         │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐                                  │
│  │P01 │ │P02 │ │P03 │ │P04 │ (Ports 8101+)                    │
│  └────┘ └────┘ └────┘ └────┘                                  │
└────────────────────────────────────────────────────────────────┘
```

### Orchestrator's Role

The Game Orchestrator is NOT another game agent - it is a **meta-layer controller** that:

1. **Manages Agent Lifecycle**: Starts, stops, restarts agents in correct order
2. **Monitors Health**: Continuous health checks with automatic recovery
3. **Controls Tournament Flow**: Triggers rounds, validates state transitions
4. **Provides Observability**: Real-time dashboard and log aggregation
5. **Handles Failures**: Automatic restart, error recovery, graceful degradation

---

## Component Design

### 1. AgentLifecycleManager

**Responsibility:** Start/stop/restart agents with dependency management

**File:** `orchestrator/src/orchestrator/lifecycle/agent_manager.py` (≤150 lines)

**Key Features:**
- Dependency-aware startup (respects agent dependencies)
- Parallel startup within same tier (all referees start simultaneously)
- Health check verification before proceeding
- Subprocess management with stdout/stderr capture

**Interface:**
```python
class AgentLifecycleManager:
    async def start_agent(agent_id: str, timeout: int = 30) -> bool
    async def start_all_agents() -> Dict[str, bool]
    async def stop_agent(agent_id: str) -> bool
    async def restart_agent(agent_id: str) -> bool
```

---

### 2. HealthMonitor

**Responsibility:** Continuous health monitoring with automatic recovery

**File:** `orchestrator/src/orchestrator/monitoring/health_monitor.py` (≤150 lines)

**Key Features:**
- Configurable check intervals
- Failure count tracking (3 failures = UNHEALTHY)
- Automatic recovery callbacks
- Non-blocking async monitoring

**Interface:**
```python
class HealthMonitor:
    async def start() -> None
    async def stop() -> None
    async def check_agent(agent_id: str, endpoint: str) -> HealthStatus
    def register_recovery_callback(agent_id: str, callback: Callable)
```

---

### 3. CommunicationVerifier

**Responsibility:** Test connectivity and protocol compliance

**File:** `orchestrator/src/orchestrator/verification/comm_verifier.py` (≤150 lines)

**Key Features:**
- Reachability testing
- JSON-RPC 2.0 protocol compliance verification
- Auth token validation
- Detailed error reporting

**Interface:**
```python
class CommunicationVerifier:
    async def verify_agent(agent_id: str, endpoint: str) -> VerificationResult
    async def verify_all_agents() -> Dict[str, VerificationResult]
```

---

### 4. TournamentController

**Responsibility:** Execute tournament flow and manage state transitions

**File:** `orchestrator/src/orchestrator/tournament/controller.py` (≤150 lines)

**Key Features:**
- State machine for tournament stages
- Round management (announcement, monitoring, completion)
- Registration verification
- Schedule creation triggering

**Interface:**
```python
class TournamentController:
    async def start_tournament() -> bool
    async def start_next_round() -> bool
    async def monitor_round_progress() -> Dict
    async def pause_tournament() -> bool
    async def resume_tournament() -> bool
```

---

### 5. DashboardServer

**Responsibility:** Real-time monitoring web interface

**File:** `orchestrator/src/orchestrator/dashboard/server.py` (≤150 lines)

**Key Features:**
- Real-time WebSocket updates
- HTML dashboard with live data
- Health status visualization
- Standings table updates
- Match progress tracking

**Interface:**
```python
class DashboardServer:
    async def start(port: int = 9000) -> None
    async def broadcast_update(update_type: str, data: Dict)
    async def get_current_state() -> Dict
```

---

### 6. ErrorRecoveryManager

**Responsibility:** Handle failures and implement recovery strategies

**File:** `orchestrator/src/orchestrator/recovery/error_manager.py` (≤150 lines)

**Key Features:**
- Pluggable recovery handlers
- Exponential backoff for retries
- Failure history tracking
- Context-aware error handling

**Interface:**
```python
class ErrorRecoveryManager:
    def register_handler(error_type: str, handler: Callable)
    async def handle_error(error_type: str, context: Dict) -> bool
    async def restart_agent(agent_id: str, max_retries: int = 3) -> bool
```

---

### 7. LogAggregator

**Responsibility:** Collect and analyze logs from all agents

**File:** `orchestrator/src/orchestrator/logging/log_aggregator.py` (≤150 lines)

**Key Features:**
- Real-time log tailing
- Structured JSON log parsing
- Error filtering by timestamp/agent
- Pattern analysis

**Interface:**
```python
class LogAggregator:
    async def tail_logs(agent_id: str, callback: Callable)
    async def get_errors(since: Optional[str], agent_id: Optional[str]) -> List[Dict]
    async def analyze_patterns() -> Dict
```

---

## Startup Sequence

### State Machine

```
INITIALIZING → STARTING_LEAGUE_MANAGER → VERIFYING_LEAGUE_MANAGER →
STARTING_REFEREES → VERIFYING_REFEREES → STARTING_PLAYERS →
VERIFYING_PLAYERS → READY → TOURNAMENT_RUNNING → COMPLETED
```

### Detailed Flow

**Stage 1: Initialize Orchestrator**
- Load configuration
- Initialize all components
- Register recovery handlers

**Stage 2: Start League Manager**
- Execute startup command
- Wait for health check (max 30s)
- Verify JSON-RPC protocol

**Stage 3: Start Referees**
- Start all referees in parallel
- Wait for health checks
- Verify registration with League Manager

**Stage 4: Start Players**
- Start all players in parallel
- Wait for health checks
- Verify registration with League Manager

**Stage 5: Verify Connectivity**
- Test communication between all agents
- Validate auth tokens
- Confirm protocol compliance

**Stage 6: Start Monitoring**
- Begin health monitoring loop
- Start log aggregation
- Launch dashboard server

**Stage 7: Start Tournament**
- Trigger schedule creation
- Announce first round
- Monitor tournament execution

---

## Tournament Flow Management

### 7-Stage Tournament Execution

**Stage 1: Referee Registration**
- Monitor League Manager for referee registrations
- Verify minimum referee count (2)
- Log registration confirmations

**Stage 2: Player Registration**
- Monitor League Manager for player registrations
- Verify minimum player count (4)
- Log registration confirmations

**Stage 3: Schedule Creation**
- Trigger League Manager to create schedule
- Verify schedule generated correctly
- Broadcast schedule to dashboard

**Stage 4: Round Announcement**
- Trigger round announcement
- Monitor announcement delivery
- Verify players acknowledged

**Stage 5: Match Execution**
- Monitor match progress in real-time
- Track match state transitions
- Log match results

**Stage 6: Round Completion**
- Wait for all matches to complete
- Verify standings updated
- Trigger next round or proceed to completion

**Stage 7: League Completion**
- Verify all rounds complete
- Archive tournament data
- Display final results on dashboard

---

## Communication Patterns

### Orchestrator → League Manager

```python
# Query standings
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "league_query",
            "params": {"query_type": "GET_STANDINGS"},
            "id": 1
        }
    )

# Start round
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/mcp",
        json={
            "jsonrpc": "2.0",
            "method": "announce_round",
            "params": {"round_id": 1},
            "id": 2
        }
    )
```

### Orchestrator → All Agents (Health Checks)

```python
# Periodic health check
for agent_id, config in agents.items():
    async with httpx.AsyncClient(timeout=2.0) as client:
        response = await client.get(f"{config.health_endpoint}")
        if response.status_code == 200:
            health_status[agent_id] = HealthStatus.HEALTHY
```

### Orchestrator → Dashboard (WebSocket)

```python
# Broadcast tournament update
await dashboard.broadcast_update("standings", {
    "round": current_round,
    "standings": standings_data
})

await dashboard.broadcast_update("health", {
    "agents": health_status
})
```

---

## Error Handling Strategies

### 1. Agent Fails to Start

**Detection:** Process exits immediately or health check fails within timeout

**Recovery Strategy:**
1. Log failure with context
2. Wait 2 seconds
3. Retry startup (max 3 attempts with exponential backoff: 2s, 4s, 8s)
4. If all retries fail, alert user and abort tournament

**Implementation:**
```python
for attempt in range(3):
    delay = 2 ** attempt
    await asyncio.sleep(delay)
    success = await self.lifecycle.start_agent(agent_id)
    if success:
        return True
return False
```

---

### 2. Agent Crashes Mid-Tournament

**Detection:** Health monitor detects UNHEALTHY status

**Recovery Strategy:**
1. Log crash with agent state
2. Pause affected matches (if referee/player)
3. Attempt automatic restart
4. Resume tournament if restart successful
5. If restart fails, manual intervention required

**Implementation:**
```python
async def _handle_agent_crash(context: Dict):
    agent_id = context["agent_id"]

    # Pause tournament if critical agent
    if agent_id == "league_manager":
        await self.tournament.pause()

    # Attempt restart
    success = await self.recovery.restart_agent(agent_id, max_retries=3)

    if success:
        await self.tournament.resume()
    else:
        await self.dashboard.broadcast_update("error", {
            "type": "AGENT_CRASH_UNRECOVERABLE",
            "agent_id": agent_id
        })
```

---

### 3. Network Timeout

**Detection:** HTTP request timeout (>30s for invitations, >30s for choices)

**Recovery Strategy:**
1. Retry request with exponential backoff
2. After 3 failures, mark agent as degraded
3. If critical path, pause tournament
4. Alert via dashboard

---

### 4. Match Timeout

**Detection:** Match doesn't complete within expected time

**Recovery Strategy:**
1. Query referee for match state
2. If referee responsive, continue waiting
3. If referee unresponsive, restart referee
4. Replay match from beginning

---

## Implementation Specifications

### File Structure

```
orchestrator/
├── src/
│   └── orchestrator/
│       ├── __init__.py
│       ├── main.py                    # Entry point (≤150 lines)
│       ├── lifecycle/
│       │   ├── __init__.py
│       │   └── agent_manager.py       # AgentLifecycleManager (≤150 lines)
│       ├── monitoring/
│       │   ├── __init__.py
│       │   └── health_monitor.py      # HealthMonitor (≤150 lines)
│       ├── verification/
│       │   ├── __init__.py
│       │   └── comm_verifier.py       # CommunicationVerifier (≤150 lines)
│       ├── tournament/
│       │   ├── __init__.py
│       │   └── controller.py          # TournamentController (≤150 lines)
│       ├── dashboard/
│       │   ├── __init__.py
│       │   ├── server.py              # DashboardServer (≤150 lines)
│       │   └── static/
│       │       ├── dashboard.html
│       │       ├── styles.css
│       │       └── app.js
│       ├── recovery/
│       │   ├── __init__.py
│       │   └── error_manager.py       # ErrorRecoveryManager (≤150 lines)
│       └── logging/
│           ├── __init__.py
│           └── log_aggregator.py      # LogAggregator (≤150 lines)
├── config/
│   ├── agents.json                     # Agent configurations
│   └── orchestrator.json               # Orchestrator settings
├── tests/
│   ├── unit/
│   │   ├── test_lifecycle.py
│   │   ├── test_health_monitor.py
│   │   ├── test_tournament_controller.py
│   │   └── test_error_recovery.py
│   └── integration/
│       ├── test_full_startup.py
│       └── test_tournament_execution.py
├── requirements.txt
├── setup.py
└── README.md
```

---

### Configuration Format

**File:** `config/agents.json`

```json
{
  "agents": [
    {
      "agent_id": "league_manager",
      "agent_type": "LEAGUE_MANAGER",
      "port": 8000,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/league_manager",
      "startup_command": ["venv/Scripts/python.exe", "-m", "league_manager.main"],
      "health_endpoint": "http://localhost:8000/health",
      "dependencies": []
    },
    {
      "agent_id": "REF01",
      "agent_type": "REFEREE",
      "port": 8001,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/referee_agent",
      "startup_command": ["venv/Scripts/python.exe", "-m", "referee.main", "--port", "8001"],
      "health_endpoint": "http://localhost:8001/health",
      "dependencies": ["league_manager"]
    },
    {
      "agent_id": "REF02",
      "agent_type": "REFEREE",
      "port": 8002,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/referee_agent",
      "startup_command": ["venv/Scripts/python.exe", "-m", "referee.main", "--port", "8002"],
      "health_endpoint": "http://localhost:8002/health",
      "dependencies": ["league_manager"]
    },
    {
      "agent_id": "P01",
      "agent_type": "PLAYER",
      "port": 8101,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/player_agent",
      "startup_command": ["venv/Scripts/python.exe", "-m", "player_agent.main", "--port", "8101"],
      "health_endpoint": "http://localhost:8101/health",
      "dependencies": ["league_manager"]
    },
    {
      "agent_id": "P02",
      "agent_type": "PLAYER",
      "port": 8102,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/player_agent",
      "startup_command": ["venv/Scripts/python.exe", "-m", "player_agent.main", "--port", "8102"],
      "health_endpoint": "http://localhost:8102/health",
      "dependencies": ["league_manager"]
    },
    {
      "agent_id": "P03",
      "agent_type": "PLAYER",
      "port": 8103,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/player_agent",
      "startup_command": ["venv/Scripts/python.exe", "-m", "player_agent.main", "--port", "8103"],
      "health_endpoint": "http://localhost:8103/health",
      "dependencies": ["league_manager"]
    },
    {
      "agent_id": "P04",
      "agent_type": "PLAYER",
      "port": 8104,
      "working_dir": "C:/AIDevelopmentCourse/L-25-TheGame/agents/player_agent",
      "startup_command": ["venv/Scripts/python.exe", "-m", "player_agent.main", "--port", "8104"],
      "health_endpoint": "http://localhost:8104/health",
      "dependencies": ["league_manager"]
    }
  ],
  "orchestrator": {
    "dashboard_port": 9000,
    "health_check_interval": 5,
    "startup_grace_period": 2,
    "agent_startup_timeout": 30
  }
}
```

---

## Testing Strategy

### Unit Tests

```python
# tests/unit/test_lifecycle.py
async def test_start_agent_with_dependencies():
    manager = AgentLifecycleManager("test_config.json")

    # Start league manager first
    success = await manager.start_agent("league_manager")
    assert success

    # Start referee (depends on league manager)
    success = await manager.start_agent("REF01")
    assert success


async def test_start_agent_missing_dependency():
    manager = AgentLifecycleManager("test_config.json")

    # Try to start referee without league manager
    with pytest.raises(AgentStartupError):
        await manager.start_agent("REF01")
```

### Integration Tests

```python
# tests/integration/test_full_startup.py
async def test_complete_startup_sequence():
    orchestrator = GameOrchestrator()

    # Run startup
    success = await orchestrator.run()
    assert success

    # Verify all agents running
    assert orchestrator.health.agent_health["league_manager"] == HealthStatus.HEALTHY
    assert orchestrator.health.agent_health["REF01"] == HealthStatus.HEALTHY
    assert orchestrator.health.agent_health["P01"] == HealthStatus.HEALTHY


async def test_recovery_from_crash():
    orchestrator = GameOrchestrator()
    await orchestrator.run()

    # Simulate agent crash
    orchestrator.lifecycle.processes["P01"].kill()

    # Wait for recovery
    await asyncio.sleep(10)

    # Verify agent restarted
    assert orchestrator.health.agent_health["P01"] == HealthStatus.HEALTHY
```

---

## Deployment Architecture

### Single Machine Deployment

```
┌──────────────────────────────────────┐
│         Host Machine (localhost)      │
│                                       │
│  ┌────────────────────────────────┐  │
│  │ Game Orchestrator (Port 9000)  │  │
│  └────────────────────────────────┘  │
│             ↕ subprocess              │
│  ┌────────────────────────────────┐  │
│  │ League Manager (Port 8000)     │  │
│  └────────────────────────────────┘  │
│  ┌───────────┐  ┌───────────┐       │
│  │ REF01     │  │ REF02     │       │
│  │ (8001)    │  │ (8002)    │       │
│  └───────────┘  └───────────┘       │
│  ┌─────┐ ┌─────┐ ┌─────┐ ┌─────┐   │
│  │ P01 │ │ P02 │ │ P03 │ │ P04 │   │
│  │8101 │ │8102 │ │8103 │ │8104 │   │
│  └─────┘ └─────┘ └─────┘ └─────┘   │
└──────────────────────────────────────┘
```

---

## Summary

The Game Orchestrator provides a production-ready solution for managing the complete Even/Odd tournament system:

**Core Capabilities:**
- ✅ Automated startup with dependency management
- ✅ Continuous health monitoring with auto-recovery
- ✅ Real-time tournament flow control
- ✅ Web dashboard for observability
- ✅ Comprehensive error handling

**Key Benefits:**
- ✅ Eliminates manual agent startup
- ✅ Ensures correct startup order
- ✅ Provides immediate visibility into system health
- ✅ Handles failures automatically
- ✅ Centralizes logging and debugging

**Implementation Ready:**
- ✅ All components ≤150 lines
- ✅ Clear separation of concerns
- ✅ Type-safe Python interfaces
- ✅ Comprehensive error handling
- ✅ Full test coverage strategy

---

## Related Documents

- [Game Orchestrator Runtime Guide](../guides/game-orchestrator-runtime-guide.md) - Operational procedures
- [Game Flow Design](./game-flow-design.md) - Complete game flow logic
- [League Manager Architecture](./league-manager-architecture.md) - League Manager implementation
- [Referee Architecture](./referee-architecture.md) - Referee implementation
- [Player Agent Architecture](./player-agent-architecture.md) - Player Agent implementation

---

**Document Status:** FINAL
**Last Updated:** 2025-12-24
**Version:** 1.0
**Author:** Architecture Review Team
