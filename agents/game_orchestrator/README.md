# Game Orchestrator

Master controller for the Even/Odd Tournament system. Manages agent lifecycle, monitors health, controls tournament flow, and provides real-time observability.

## Overview

The Game Orchestrator is a meta-layer controller that coordinates all game agents:
- **League Manager** (Tournament coordinator)
- **Referees** (Game executors)
- **Players** (AI agents)

### Key Features

- **Automated Startup**: Dependency-aware agent startup (League Manager → Referees → Players)
- **Health Monitoring**: Continuous health checks with automatic recovery
- **Tournament Control**: 7-stage tournament flow management
- **Real-time Dashboard**: WebSocket-based monitoring interface
- **Error Recovery**: Automatic restart with exponential backoff
- **Log Aggregation**: Centralized logging and error analysis

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                  GAME ORCHESTRATOR                          │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Lifecycle    │  │ Health       │  │ Dashboard    │     │
│  │ Manager      │  │ Monitor      │  │ Server       │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Tournament   │  │ Error        │  │ Log          │     │
│  │ Controller   │  │ Recovery     │  │ Aggregator   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────────────────────────────────────────┘
                            ↕
┌────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                            │
│  League Manager → Referees → Players                        │
└────────────────────────────────────────────────────────────┘
```

## Installation

### Prerequisites

- Python 3.11+
- All agent implementations (League Manager, Referees, Players)
- Ports 8000-8104 and 9000 available

### Setup

```bash
cd agents/game_orchestrator

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

## Configuration

Edit `config/agents.json` to configure agents:

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
    // ... more agents
  ],
  "orchestrator": {
    "dashboard_port": 9000,
    "health_check_interval": 5,
    "startup_grace_period": 2,
    "agent_startup_timeout": 30
  }
}
```

### Configuration Fields

| Field | Description |
|-------|-------------|
| `agent_id` | Unique identifier for the agent |
| `agent_type` | LEAGUE_MANAGER, REFEREE, or PLAYER |
| `port` | HTTP port for the agent |
| `working_dir` | Agent's working directory (absolute path) |
| `startup_command` | Command to start the agent |
| `health_endpoint` | Health check endpoint URL |
| `dependencies` | List of agent_ids that must start first |

## Usage

### Basic Usage

```bash
cd agents/game_orchestrator
source venv/bin/activate  # Windows: venv\Scripts\activate

# Run with default configuration
python -m orchestrator.main

# Run with custom configuration
python -m orchestrator.main --config path/to/config.json
```

### Startup Sequence

The orchestrator executes these 7 stages:

1. **Start League Manager** - Waits for health check
2. **Start Referees** - All referees start in parallel
3. **Start Players** - All players start in parallel
4. **Verify Communication** - Tests JSON-RPC 2.0 compliance
5. **Start Health Monitoring** - Begins continuous health checks
6. **Start Dashboard** - Launches web interface on port 9000
7. **Start Tournament** - Triggers tournament execution

### Accessing the Dashboard

Once the orchestrator is running, open your browser to:

```
http://localhost:9000
```

The dashboard displays:
- Real-time agent health status
- Tournament standings
- Current round progress
- Error alerts

### Monitoring

**View orchestrator logs:**
```bash
# Real-time logs
tail -f SHARED/logs/orchestrator/orchestrator.log.jsonl | jq '.'

# Filter errors
tail -f SHARED/logs/orchestrator/orchestrator.log.jsonl | jq 'select(.level == "ERROR")'
```

**Check agent health:**
```bash
# Test individual agent
curl http://localhost:8000/health  # League Manager
curl http://localhost:8001/health  # Referee 1
curl http://localhost:8101/health  # Player 1

# All agents
for port in 8000 8001 8002 8101 8102 8103 8104; do
    echo -n "Port $port: "
    curl -s http://localhost:$port/health || echo "Not responding"
done
```

## Components

### 1. AgentLifecycleManager

Manages agent startup, shutdown, and restarts.

**Key Methods:**
- `start_agent(agent_id)` - Start single agent
- `start_all_agents()` - Start all agents in dependency order
- `stop_agent(agent_id)` - Stop running agent
- `restart_agent(agent_id)` - Restart agent

### 2. HealthMonitor

Continuous health monitoring with automatic recovery.

**Features:**
- Configurable check intervals (default: 5 seconds)
- Failure threshold tracking (3 failures = UNHEALTHY)
- Recovery callback triggers
- Non-blocking async monitoring

### 3. CommunicationVerifier

Tests agent connectivity and protocol compliance.

**Verifies:**
- Agent reachability
- JSON-RPC 2.0 protocol compliance
- MCP handshake success

### 4. TournamentController

Controls tournament flow and state transitions.

**State Machine:**
```
INITIALIZING → REGISTERING → SCHEDULED →
ROUND_ANNOUNCED → ROUND_IN_PROGRESS →
ROUND_COMPLETED → TOURNAMENT_COMPLETED
```

**Key Methods:**
- `start_tournament()` - Initialize tournament
- `start_next_round()` - Announce next round
- `monitor_round_progress()` - Get current standings
- `pause_tournament()` / `resume_tournament()` - Pause/resume

### 5. DashboardServer

Real-time web interface with WebSocket updates.

**Features:**
- Live agent health status
- Tournament standings table
- Match progress tracking
- Error notifications

### 6. ErrorRecoveryManager

Handles failures with pluggable recovery strategies.

**Features:**
- Exponential backoff retries (2s, 4s, 8s)
- Failure history tracking
- Custom error handlers
- Agent restart orchestration

### 7. LogAggregator

Collects and analyzes logs from all agents.

**Features:**
- Real-time log tailing
- Error filtering by timestamp/agent
- Pattern analysis
- Aggregated error statistics

## Error Handling

### Automatic Recovery

The orchestrator automatically handles:

1. **Agent Crashes** - Restart with exponential backoff (max 3 attempts)
2. **Health Check Failures** - Triggers recovery after 3 consecutive failures
3. **Network Timeouts** - Retries with backoff
4. **Tournament Pausing** - Pauses tournament during critical agent recovery

### Manual Intervention

If automatic recovery fails:

1. Check agent logs: `SHARED/logs/agents/{agent_id}.log.jsonl`
2. Verify configuration: `config/agents.json`
3. Test agent manually:
   ```bash
   cd agents/{agent_directory}
   source venv/bin/activate
   python -m {module}.main --port {port}
   ```
4. Restart orchestrator

## Testing

### Run Unit Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html --cov-report=term

# Specific component
pytest tests/unit/test_lifecycle.py
pytest tests/unit/test_health_monitor.py
pytest tests/unit/test_tournament_controller.py
```

### Run Integration Tests

```bash
# Full startup sequence
pytest tests/integration/test_full_startup.py

# Tournament execution
pytest tests/integration/test_tournament_execution.py
```

### Manual Testing

```bash
# Test configuration loading
python -c "from orchestrator.config import Config; c = Config('config/agents.json'); print(c.agents)"

# Test agent startup
python -c "
import asyncio
from orchestrator.config import Config
from orchestrator.lifecycle.agent_manager import AgentLifecycleManager

async def test():
    c = Config('config/agents.json')
    mgr = AgentLifecycleManager(c.agents)
    await mgr.start_agent('league_manager')

asyncio.run(test())
"
```

## Troubleshooting

### Issue: Agent fails to start

**Symptoms:** `AgentStartupError: Agent crashed on startup`

**Solutions:**
1. Check agent's working directory exists
2. Verify startup command is correct
3. Test agent can run independently
4. Check agent logs for errors

### Issue: Health check fails

**Symptoms:** Agent marked UNHEALTHY after 3 failures

**Solutions:**
1. Verify agent is listening on correct port
2. Check firewall isn't blocking ports
3. Increase `health_check_interval` if system is slow
4. Check agent's `/health` endpoint directly

### Issue: Communication verification fails

**Symptoms:** `Agent verification failed: Protocol check failed`

**Solutions:**
1. Verify agent implements MCP protocol
2. Check JSON-RPC 2.0 compliance
3. Test with manual JSON-RPC request:
   ```bash
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"initialize","params":{},"id":1}'
   ```

### Issue: Tournament doesn't progress

**Symptoms:** Orchestrator starts but tournament stays in INITIALIZING

**Solutions:**
1. Check League Manager is running and healthy
2. Verify schedule exists: Query League Manager's `GET_SCHEDULE`
3. Check for errors in orchestrator logs
4. Ensure all players and referees registered

## Development

### Code Structure

```
game_orchestrator/
├── src/
│   └── orchestrator/
│       ├── main.py                    # Entry point
│       ├── config.py                  # Configuration management
│       ├── lifecycle/
│       │   └── agent_manager.py       # Agent startup/shutdown
│       ├── monitoring/
│       │   └── health_monitor.py      # Health checks
│       ├── verification/
│       │   └── comm_verifier.py       # Protocol verification
│       ├── tournament/
│       │   └── controller.py          # Tournament flow
│       ├── dashboard/
│       │   ├── server.py              # Web interface
│       │   └── static/
│       │       └── dashboard.html     # Dashboard HTML
│       ├── recovery/
│       │   └── error_manager.py       # Error handling
│       └── logging_utils/
│           └── log_aggregator.py      # Log collection
├── config/
│   └── agents.json                     # Agent configuration
├── tests/
│   ├── unit/                           # Unit tests
│   └── integration/                    # Integration tests
├── requirements.txt                    # Dependencies
├── setup.py                            # Package metadata
└── README.md                           # This file
```

### File Size Standards

All files must be ≤150 lines (excluding blanks/comments). Check with:

```bash
# Count lines (excluding blanks and comments)
grep -v '^\s*#' file.py | grep -v '^\s*$' | wc -l
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type check
mypy src/
```

## Performance

### Resource Usage

- **CPU**: Low (primarily I/O bound)
- **Memory**: ~50-100 MB (depends on number of agents)
- **Network**: HTTP polling every 5 seconds per agent

### Scalability

- **Agents**: Tested with up to 20 agents (1 League Manager, 5 Referees, 14 Players)
- **Health Checks**: Scales linearly with agent count
- **Dashboard**: Supports multiple concurrent WebSocket clients

### Optimization Tips

1. Increase `health_check_interval` for large deployments (10-15 seconds)
2. Use faster startup grace periods if agents start quickly
3. Reduce `agent_startup_timeout` for faster failure detection
4. Deploy dashboard on separate machine for production

## Related Documentation

- [Game Orchestrator Architecture](../../docs/architecture/game-orchestrator-architecture.md)
- [Game Flow Design](../../docs/architecture/game-flow-design.md)
- [Orchestrator Runtime Guide](../../docs/guides/game-orchestrator-runtime-guide.md)
- [League Manager Architecture](../../docs/architecture/league-manager-architecture.md)
- [Referee Architecture](../../docs/architecture/referee-architecture.md)
- [Player Agent Architecture](../../docs/architecture/player-agent-architecture.md)

## License

MIT License

## Version

1.0.0 - Initial Release

---

**Last Updated:** 2025-12-28
**Status:** Production Ready
