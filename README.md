# Even/Odd Tournament Game

A multi-agent AI tournament system where autonomous agents compete in the "Even/Odd" game. The system orchestrates complete round-robin tournaments with real-time monitoring and automated match execution.

## Quick Start

### Run a Complete Tournament

```bash
# Windows
scripts\run-tournament.bat

# Linux/Mac
scripts/run-tournament.sh
```

**Access the Dashboard**: Open http://localhost:9000 in your browser to watch the tournament in real-time.

### What Happens

1. Game Orchestrator starts and validates the environment
2. League Manager initializes on port 8000
3. Two Referees (REF01, REF02) start on ports 8001-8002
4. Four Players (P01-P04) start on ports 8101-8104
5. All agents register with the League Manager
6. Round-robin schedule is generated (6 matches)
7. Tournament executes with live dashboard updates
8. Final standings are displayed

---

## The Game: Even/Odd

### Rules

- **Players**: 2 per match (simultaneous play)
- **Move**: Each player chooses "even" or "odd"
- **Random Draw**: System generates random integer 1-10
- **Winner Determination**: Player whose choice matches the number's parity wins
  - Example: Number is 7 (odd) → Player who chose "odd" wins
  - If both chose same parity → Tie

### Scoring

| Result | Points |
|--------|--------|
| Win    | 3      |
| Tie    | 1      |
| Loss   | 0      |

### Tournament Format

- **Round-robin**: Every player faces every other player once
- **4 Players**: 6 total matches across 3 rounds
- **Concurrent Matches**: Multiple matches run in parallel when possible
- **Ranking**: By total points (tiebreakers: head-to-head, wins, then player_id)

---

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Game Orchestrator                         │
│  - Agent Lifecycle Management                                │
│  - Health Monitoring & Auto-Recovery                         │
│  - Real-time Dashboard (WebSocket)                           │
└─────────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                ▼             ▼             ▼
        ┌──────────────┐ ┌─────────┐ ┌─────────┐
        │    League    │ │ Referee │ │ Referee │
        │   Manager    │ │  REF01  │ │  REF02  │
        │  (port 8000) │ │ (8001)  │ │ (8002)  │
        └──────────────┘ └─────────┘ └─────────┘
                │             │           │
        ┌───────┼─────────────┴───────────┘
        ▼       ▼       ▼       ▼
    ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
    │ P01  │ │ P02  │ │ P03  │ │ P04  │
    │ 8101 │ │ 8102 │ │ 8103 │ │ 8104 │
    └──────┘ └──────┘ └──────┘ └──────┘
```

### Communication Protocol

All agents communicate using **MCP (Model Context Protocol)** over HTTP:
- **Transport**: JSON-RPC 2.0
- **Framework**: FastAPI (async)
- **Validation**: Pydantic schemas

---

## Agents and Participants

### 1. Game Orchestrator (Master Controller)

**Port**: None (manages other agents)
**Role**: System coordinator and monitor

**Responsibilities**:
- Start/stop all agents in correct dependency order
- Continuous health monitoring (5-second intervals)
- Automatic recovery on agent failures
- WebSocket dashboard for real-time monitoring
- Centralized log aggregation

**Components**:
- AgentLifecycleManager
- HealthMonitor
- DashboardServer
- ErrorRecoveryManager
- LogAggregator

**Location**: `agents/game_orchestrator/`

---

### 2. League Manager (Tournament Controller)

**Port**: 8000
**Endpoint**: http://localhost:8000/mcp

**Role**: Tournament organizer and registry

**Responsibilities**:
- Player and referee registration
- Round-robin schedule generation
- Standings calculation with tiebreakers
- Round announcements and completion tracking
- Broadcasting updates to all participants
- Persistent data storage (players, standings, schedule)

**MCP Tools**:
- `register_player` - Player registration
- `register_referee` - Referee registration
- `get_standings` - Current tournament rankings
- `get_schedule` - Match schedule
- `report_match_result` - Record match outcomes

**Location**: `agents/league_manager/`
**Data**: `agents/league_manager/SHARED/data/leagues/league_2025_even_odd/`

---

### 3. Referees (Match Orchestrators)

**Instances**: REF01 (port 8001), REF02 (port 8002)
**Endpoints**:
- http://localhost:8001/mcp
- http://localhost:8002/mcp

**Role**: Match execution and validation

**Responsibilities**:
- Conduct individual matches (6-phase flow)
- Enforce timeouts (5s invitation, 30s choice)
- Simultaneous move collection (fair play)
- Cryptographic random number generation
- Winner determination (parity matching)
- Result reporting to League Manager

**Match Flow (6 Phases)**:
1. **IDLE** → Waiting for match assignment
2. **INVITING** → Send invitations to both players (5s timeout)
3. **WAITING_FOR_CHOICES** → Collect simultaneous choices (30s timeout)
4. **EVALUATING** → Generate random number, determine winner
5. **NOTIFYING** → Send results to players
6. **FINISHED** → Report to League Manager

**MCP Tools**:
- `conduct_match` - Execute complete match

**Location**: `agents/referee_agent/`

---

### 4. Players (Game Participants)

**Instances**: P01-P04 (ports 8101-8104)
**Endpoints**: http://localhost:8101-8104/mcp

**Role**: Tournament competitors

**Responsibilities**:
- Accept/reject match invitations (5s timeout)
- Choose parity ("even" or "odd") strategically (30s timeout)
- Acknowledge match results
- Maintain game history (optional, for adaptive strategies)

**Current Strategy**: RandomStrategy (baseline implementation)
- Randomly selects "even" or "odd" with 50/50 probability
- Guaranteed to respond within timeout limits
- Serves as fallback for more advanced strategies

**MCP Tools**:
- `handle_game_invitation` - Accept/reject match invitations
- `choose_parity` - Strategic choice (even/odd)
- `notify_match_result` - Receive match outcomes

**Location**: `agents/player_agent/`

---

## Game Flow

### Complete Tournament Flow

```
1. STARTUP
   └─> Orchestrator starts all agents
   └─> Agents perform health checks
   └─> Dashboard becomes available

2. REGISTRATION
   └─> 4 Players register with League Manager
   └─> 2 Referees register with League Manager
   └─> League Manager confirms all participants

3. SCHEDULING
   └─> League Manager generates round-robin schedule
   └─> 6 matches distributed across 3 rounds
   └─> 2 referees assigned (alternating)

4. TOURNAMENT EXECUTION (3 rounds)
   ├─> Round 1: P01 vs P02 (REF01), P03 vs P04 (REF02)
   ├─> Round 2: P01 vs P03 (REF01), P02 vs P04 (REF02)
   └─> Round 3: P01 vs P04 (REF01), P02 vs P03 (REF02)

5. STANDINGS UPDATE
   └─> After each match, League Manager recalculates standings
   └─> Rankings updated based on points and tiebreakers

6. COMPLETION
   └─> Final standings displayed
   └─> Champion determined
   └─> All logs saved to SHARED/logs/tournaments/
```

### Individual Match Flow

```
┌──────────────┐
│   Referee    │
│  (REF01/02)  │
└──────┬───────┘
       │
       ├─> 1. INVITING (5s timeout)
       │   ├─> Send invitation to Player A
       │   └─> Send invitation to Player B
       │
       ├─> 2. WAITING_FOR_CHOICES (30s timeout)
       │   ├─> Player A chooses parity
       │   └─> Player B chooses parity
       │   └─> Simultaneous collection (asyncio.gather)
       │
       ├─> 3. EVALUATING
       │   ├─> Generate random number (1-10, cryptographic)
       │   ├─> Determine number parity
       │   └─> Match against player choices
       │
       ├─> 4. NOTIFYING
       │   ├─> Send result to Player A
       │   └─> Send result to Player B
       │
       └─> 5. REPORTING
           └─> Report result to League Manager
           └─> Update standings
```

---

## Dashboard Features

**URL**: http://localhost:9000

### Real-time Monitoring

- **Tournament Status**: Current phase (startup, registration, execution, completed)
- **Live Standings**: Updated after each match
  - Player rankings
  - Points, wins, losses, draws
  - Match history
- **Active Matches**: In-progress matches with status
- **Agent Health**: Status of all 7 agents (✓ healthy, ✗ unhealthy)
- **System Logs**: Live log stream via WebSocket

### Technology

- **Backend**: FastAPI (integrated into orchestrator)
- **Frontend**: HTML5 + JavaScript
- **Updates**: WebSocket (ws://localhost:9000/ws)
- **Refresh Rate**: 1-second intervals

---

## Requirements

### System Requirements

- **Python**: 3.11 or higher
- **OS**: Windows, Linux, or macOS
- **Memory**: 2GB RAM minimum
- **Ports**: 8000-8002, 8101-8104, 9000 (must be available)

### Python Dependencies

Core packages (see `requirements.txt` in each agent):
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `httpx` - HTTP client (async)
- `pytest` - Testing framework
- `pytest-asyncio` - Async test support

### Installation

Each agent uses isolated virtual environments:

```bash
# Player Agent
cd agents/player_agent
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
pip install -e .

# Repeat for league_manager, referee_agent, game_orchestrator
```

**Note**: The tournament launcher (`scripts/run-tournament.bat`) automatically handles all startup.

---

## Project Structure

```
L-25-TheGame/
├── README.md                    # This file
├── CLAUDE.md                    # AI agent quick reference
│
├── agents/                      # Agent implementations
│   ├── player_agent/           # Player (Phase 1)
│   │   ├── venv/               # Isolated Python environment
│   │   ├── src/player_agent/   # Implementation
│   │   ├── tests/              # 152 tests, 90% coverage
│   │   └── requirements.txt
│   │
│   ├── league_manager/         # Tournament controller (Phase 2)
│   │   └── SHARED/data/leagues/league_2025_even_odd/
│   │       ├── players.json    # Registered players
│   │       ├── standings.json  # Current rankings
│   │       └── schedule.json   # Match schedule
│   │
│   ├── referee_agent/          # Match orchestrator (Phase 3)
│   │
│   └── game_orchestrator/      # Master controller
│       ├── config/agents.json  # Agent configuration
│       └── src/orchestrator/
│           ├── dashboard_server.py
│           ├── health_monitor.py
│           └── tournament_controller.py
│
├── SHARED/                     # Shared resources
│   ├── logs/                   # All tournament logs
│   │   ├── tournaments/        # Tournament execution logs
│   │   ├── orchestrator/       # System logs
│   │   ├── league/             # League Manager logs
│   │   ├── referees/           # Referee logs
│   │   └── players/            # Player logs
│   │
│   └── league_sdk/             # Shared Python SDK
│       └── models/             # Pydantic schemas
│
├── docs/                       # Documentation
│   ├── architecture/           # 12 architecture documents
│   ├── requirements/           # 6 PRD documents
│   ├── standards/              # Implementation standards
│   └── guides/                 # User guides
│
└── scripts/                    # Utility scripts
    └── run-tournament.bat      # Main tournament launcher
```

---

## Logs and Data

### Log Locations

All logs are centralized in `SHARED/logs/`:

- **Tournament Logs**: `SHARED/logs/tournaments/tournament_*.log`
- **Orchestrator Logs**: `SHARED/logs/orchestrator/`
- **Agent Logs**: `SHARED/logs/league/`, `SHARED/logs/referees/`, `SHARED/logs/players/`

**Format**: JSON Lines (JSONL) for structured parsing

### Persistent Data

League Manager stores tournament state:
- **Players**: `agents/league_manager/SHARED/data/leagues/league_2025_even_odd/players.json`
- **Standings**: `agents/league_manager/SHARED/data/leagues/league_2025_even_odd/standings.json`
- **Schedule**: `agents/league_manager/SHARED/data/leagues/league_2025_even_odd/schedule.json`

**Note**: Clear these files between tournaments to reset player IDs:
```bash
rm agents/league_manager/SHARED/data/leagues/league_2025_even_odd/*.json
```

---

## Testing

### Test Coverage

- **Total Tests**: 152 (90% pass rate)
- **Unit Tests**: 89 tests
- **Integration Tests**: 66 tests across 10 files
- **Coverage**: Player Agent 83%, League Manager 72%, Referee 68%

### Run Tests

```bash
# Player Agent
cd agents/player_agent
venv\Scripts\activate
pytest --cov=src --cov-report=term

# All agents
pytest tests/integration/ -v
```

### Test Categories

- **MCP Protocol Tests**: JSON-RPC 2.0 compliance
- **Timeout Tests**: Invitation (5s), Choice (30s) enforcement
- **Match Flow Tests**: Complete match execution
- **Tournament Tests**: Round-robin scheduling, standings calculation
- **Error Recovery Tests**: Agent failures, network issues

---

## Troubleshooting

### Common Issues

**Port Already in Use**
```
Error: Address already in use (port 8000)
Solution: Kill existing processes or change ports in agents.json
```

**Player ID Confusion (P05, P11 instead of P01-P04)**
```
Cause: League Manager persists data across runs
Solution: Clear persistent data before new tournament
  rm agents/league_manager/SHARED/data/leagues/league_2025_even_odd/*.json
```

**Dashboard Not Accessible**
```
Check: http://localhost:9000
Solution: Ensure orchestrator started successfully
  Check logs in SHARED/logs/orchestrator/
```

**Agent Failed to Start**
```
Check: Virtual environment activated
  cd agents/player_agent && venv\Scripts\activate
Check: Dependencies installed
  pip install -r requirements.txt
```

**Timeout Errors in Matches**
```
Cause: Agent response exceeds timeout limit
Solution: Check agent logs for performance issues
  Player choice must complete within 30s
  Invitation response within 5s
```

---

## Development

### Phase Completion Status

- ✅ **Phase 1**: Player Agent (8/8 tasks, 100%)
- ✅ **Phase 2**: League Manager (8/8 tasks, 100%)
- ✅ **Phase 3**: Referee (9/9 tasks, 100%)
- ✅ **Phase 4**: System Integration (10/10 tasks, 100%)
- ✅ **Game Orchestrator**: Master Controller (7/7 components, 100%)
- ⏳ **Phase 5**: Player Intelligence (0/7 tasks) - Future
- ⏳ **Phase 6**: LLM Enhancement (0/6 tasks) - Optional

### Documentation

- **Quick Start**: `IMPLEMENTATION-QUICK-START.md`
- **Architecture Index**: `docs/architecture/ARCHITECTURE-INDEX.md`
- **Implementation Standards**: `docs/standards/implementation-standards.md`
- **Agent Guides**: See individual agent README files

### Contributing

All contributions must follow:
- **File Size Limit**: ≤150 lines per file
- **Test Coverage**: ≥80%
- **Documentation**: Google-style docstrings
- **Type Hints**: All function signatures
- **Logging**: Structured JSON logging

See `docs/standards/implementation-standards.md` for complete requirements.

---

## Credits

**Project**: L-25 AI Development Course - The Game
**Architecture**: Multi-agent MCP system
**Protocol**: Model Context Protocol (JSON-RPC 2.0)
**Framework**: FastAPI + asyncio
**Version**: 5.0 (Core System Complete)
**Last Updated**: 2025-12-28

---

## License

See project documentation for license details.

---

## Support

For issues, questions, or contributions:
- Review documentation in `docs/`
- Check `CLAUDE.md` for AI agent quick reference
- See troubleshooting section above
- Review agent-specific README files

**Happy Gaming!** 🎮
