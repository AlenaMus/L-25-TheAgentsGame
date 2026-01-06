# League Manager

Top-level tournament orchestrator for the Even/Odd game league.

## Overview

The League Manager is responsible for:
- Player and referee registration
- Round-robin tournament scheduling
- Standings calculation and tracking
- Match coordination
- Tournament lifecycle management

## Installation

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install as editable package
pip install -e .
```

## Configuration

Create a `.env` file in this directory:

```env
HOST=0.0.0.0
PORT=8000
LEAGUE_ID=league_2025_even_odd
MAX_PLAYERS=50
MAX_REFEREES=10
ENV=development
```

## Running

```bash
# Using installed command
league-manager

# Or directly with uvicorn
uvicorn league_manager.main:app --host 0.0.0.0 --port 8000 --reload
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=league_manager --cov-report=html

# Run specific test file
pytest tests/unit/test_scheduler.py
```

## API Endpoints

### POST /mcp

MCP JSON-RPC endpoint for all operations:

- `register_player` - Register a player
- `register_referee` - Register a referee
- `start_league` - Start the tournament
- `report_match_result` - Report match result from referee
- `get_standings` - Get current standings

## Architecture

```
league_manager/
├── handlers/          # MCP tool handlers
│   ├── player_registration.py
│   ├── referee_registration.py
│   ├── match_result.py
│   └── league_query.py
├── scheduler/         # Scheduling logic
│   ├── round_robin.py
│   └── referee_assigner.py
├── standings/         # Standings calculation
│   └── calculator.py
├── storage/           # Data persistence
│   ├── agent_registry.py
│   └── league_store.py
└── utils/            # Utilities
    └── logger.py
```

## Data Storage

All data is stored in `SHARED/data/leagues/{league_id}/`:

- `players.json` - Registered players
- `referees.json` - Registered referees
- `schedule.json` - Tournament schedule
- `standings.json` - Current standings

## Logs

Logs are written to `SHARED/logs/league/league_manager.log.jsonl` in JSON Lines format.

## Development

### Code Standards

- All files must be ≤150 lines
- All functions must have docstrings
- Type hints required
- Structured JSON logging
- >80% test coverage

### Validation

```bash
# Validate code standards
python ../../scripts/validate_standards.py .

# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

## License

AI Development Course - Educational Use
