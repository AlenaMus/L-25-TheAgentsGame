# Player Agent P01

Player Agent for Even/Odd League Tournament

## Setup

### 1. Create Virtual Environment

```bash
cd agents/player_agent
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
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
# Edit .env with your configuration
```

### 4. Run Agent

```bash
python -m player_agent.main
```

## Development

### Run Tests

```bash
pytest tests/
```

### Format Code

```bash
black src/ tests/
ruff check src/ tests/
```

### Validate Standards

```bash
python scripts/validate_standards.py agents/player_agent
```

## Project Structure

```
player_agent/
├── venv/                 # Virtual environment
├── requirements.txt      # Dependencies
├── setup.py             # Package configuration
├── README.md            # This file
├── .env.example         # Environment template
├── src/
│   └── player_agent/
│       ├── main.py      # Entry point
│       ├── config.py    # Configuration
│       ├── handlers/    # MCP tool handlers
│       ├── strategies/  # Strategy implementations
│       ├── storage/     # Data persistence
│       └── utils/       # Utilities
└── tests/
    ├── unit/            # Unit tests
    └── integration/     # Integration tests
```

## Standards Compliance

This agent follows **implementation-standards.md**:

- ✅ Isolated virtual environment
- ✅ Proper package structure
- ✅ Files ≤150 lines
- ✅ All functions documented
- ✅ Structured JSON logging
- ✅ Follows project folder structure

Created: 2025-12-21
