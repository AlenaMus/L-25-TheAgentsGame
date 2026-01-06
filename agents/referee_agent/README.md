# Referee Agent (REF01)

Referee agent for orchestrating Even/Odd game matches in the tournament league system.

## Overview

The referee is responsible for:
- Receiving match assignments from League Manager
- Sending game invitations to players
- Collecting parity choices simultaneously (critical for fairness)
- Drawing cryptographically random numbers (1-10)
- Determining winners and calculating scores
- Notifying players of results
- Reporting outcomes to League Manager

## Architecture

### 6-Phase Match Flow

1. **Invitations**: Send GAME_INVITATION to both players (5s timeout)
2. **Choice Collection**: Request parity choices simultaneously (30s timeout)
3. **Number Drawing**: Generate cryptographic random number 1-10
4. **Evaluation**: Determine winner based on parity match
5. **Notification**: Send GAME_OVER to both players
6. **Reporting**: Report MATCH_RESULT_REPORT to League Manager

### Components

```
src/referee/
├── main.py                  # MCP server and entry point
├── config.py                # Configuration management
├── game_orchestrator.py     # 6-phase match flow
├── mcp_client.py            # HTTP client for calling tools
├── handlers/
│   └── match_assignment.py  # Handle match assignments
├── game_logic/
│   ├── state_machine.py     # Game state transitions
│   ├── rng.py              # Cryptographic random number
│   └── scorer.py           # Winner determination
└── utils/
    ├── logger.py           # Structured JSON logging
    └── helpers.py          # Utility functions
```

## Setup

### 1. Create Virtual Environment

```bash
cd agents/referee_REF01
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
pip install -e .
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=referee --cov-report=html --cov-report=term

# Run only unit tests
pytest tests/unit/

# Run integration tests
pytest tests/integration/
```

## Running the Referee

### Start Server

```bash
# Using Python module
python -m referee.main

# Using entry point
referee-ref01

# With custom port
REFEREE_PORT=8002 python -m referee.main
```

### Health Check

```bash
curl http://localhost:8001/health
```

Expected response:
```json
{
  "status": "healthy",
  "referee_id": "REF01",
  "port": 8001,
  "tools": ["assign_match"]
}
```

### Register with League Manager

The referee will automatically register when started. Manual registration:

```bash
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "register_referee",
    "params": {
      "protocol": "league.v2",
      "message_type": "REFEREE_REGISTER_REQUEST",
      "sender": "referee:REF01",
      "referee_meta": {
        "display_name": "Referee Alpha",
        "version": "1.0.0",
        "game_types": ["even_odd"],
        "contact_endpoint": "http://localhost:8001/mcp",
        "max_concurrent_matches": 2
      }
    },
    "id": 1
  }'
```

## Game Orchestration

### Match Assignment

League Manager assigns a match:

```json
{
  "jsonrpc": "2.0",
  "method": "assign_match",
  "params": {
    "match_id": "R1M1",
    "round_id": "1",
    "player_A_id": "P01",
    "player_B_id": "P02",
    "player_A_endpoint": "http://localhost:8101/mcp",
    "player_B_endpoint": "http://localhost:8102/mcp"
  },
  "id": 1
}
```

### Simultaneous Move Collection

**CRITICAL**: The referee uses `asyncio.gather()` to collect choices from both players simultaneously, ensuring fairness:

```python
results = await asyncio.gather(
    call_player_A(),
    call_player_B()
)
```

This prevents timing-based advantages.

## Configuration

Environment variables (`.env`):

```bash
REFEREE_ID=REF01
REFEREE_PORT=8001
REFEREE_DISPLAY_NAME=Referee Alpha
LEAGUE_MANAGER_ENDPOINT=http://localhost:8000/mcp
MAX_CONCURRENT_MATCHES=2
INVITATION_TIMEOUT=5
CHOICE_TIMEOUT=30
```

## Logging

Logs are written to:
- Console: Human-readable format (development)
- File: JSON Lines format at `SHARED/logs/agents/REF01.log.jsonl`

Example log entry:
```json
{
  "timestamp": "2025-12-24T10:15:00Z",
  "level": "INFO",
  "agent_id": "REF01",
  "module": "game_orchestrator",
  "function": "orchestrate_game",
  "line": 47,
  "message": "Starting game orchestration",
  "match_id": "R1M1"
}
```

## Error Handling

The referee handles errors gracefully:
- **Player timeout**: Award technical loss, report to league
- **Invalid choice**: Award technical loss to invalid player
- **Connection error**: Retry with exponential backoff
- **Game abort**: Report aborted match to League Manager

## Testing

### Unit Tests

Tests individual components:
- State machine transitions
- Random number generation
- Winner determination

```bash
pytest tests/unit/ -v
```

### Integration Tests

Tests complete match flow:
- End-to-end game orchestration
- Mock player interactions
- Timeout handling

```bash
pytest tests/integration/ -v
```

### Test Coverage

Current coverage: 85%+ (target: >80%)

```bash
pytest --cov=referee --cov-report=html
open htmlcov/index.html
```

## Development

### Code Standards

- Maximum 150 lines per file
- Type hints on all functions
- Docstrings (Google style)
- Black formatting
- Ruff linting

### Pre-commit Checks

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests
pytest
```

## Troubleshooting

### Common Issues

**Referee not receiving match assignments**
- Check League Manager is running
- Verify registration was successful
- Check network connectivity

**Player timeouts**
- Increase timeout values in `.env`
- Check player agents are running
- Verify player endpoints are correct

**Invalid state transitions**
- Check logs for state transition history
- Verify game flow is following 6-phase sequence
- Look for exceptions in orchestration

## Architecture References

- `docs/architecture/referee-architecture.md` - Complete architecture
- `docs/architecture/game-flow-design.md` - Match flow details
- `docs/architecture/common-design.md` - MCP patterns

## License

AI Development Course - Educational Use
