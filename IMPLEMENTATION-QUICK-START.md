# Implementation Quick Start Guide

**Last Updated:** 2025-12-20
**Status:** MANDATORY FOR ALL IMPLEMENTATIONS

---

## 🚀 Quick Start: Create Your First Agent

### Step 1: Generate Agent Template

```bash
# Create a player agent
python scripts/create_agent_template.py player P01

# Create a referee
python scripts/create_agent_template.py referee REF01

# Create league manager
python scripts/create_agent_template.py league_manager
```

### Step 2: Setup Virtual Environment

```bash
cd agents/player_P01

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install agent as package (editable mode)
pip install -e .
```

### Step 4: Start Coding

```bash
# Your code goes in:
src/player_agent/

# Follow these rules:
# ✅ Max 150 lines per file
# ✅ All functions have docstrings
# ✅ Use logging everywhere
# ✅ Follow folder structure guide
```

---

## 📋 MANDATORY Standards (Read This First!)

### 1. Virtual Environment (venv)

**Rule:** Each agent MUST have its own venv.

**Why:** Prevents dependency conflicts, enables isolation.

**How:**
```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

### 2. Package Structure

**Rule:** Every agent is a proper Python package with `setup.py`.

**Structure:**
```
agents/player_P01/
├── venv/                 # Virtual environment
├── requirements.txt      # Dependencies
├── setup.py             # MANDATORY - Makes it a package
├── src/
│   └── player_agent/    # Your code here
└── tests/               # Your tests here
```

### 3. File Size Limit: 150 Lines

**Rule:** No file can exceed 150 lines (excluding blanks/comments).

**Why:** Forces modularity, easier to understand.

**How to Check:**
```bash
# Count lines (excluding blanks and comments)
grep -v '^\s*#' file.py | grep -v '^\s*$' | wc -l
```

**If File is Too Large:**
- Split into multiple files
- Extract helper functions
- Create subpackages

**Example:**
```
❌ BAD: handlers.py (300 lines)

✅ GOOD:
handlers/
├── invitation.py   (80 lines)
├── choice.py       (120 lines)
└── result.py       (50 lines)
```

### 4. Documentation

**Rule:** Every function MUST have a docstring (Google style).

**Template:**
```python
def choose_parity(match_id: str, opponent_id: str) -> str:
    """
    Choose parity based on strategy.

    Args:
        match_id: Unique match identifier
        opponent_id: Opponent's player ID

    Returns:
        str: Either "even" or "odd"

    Raises:
        ValueError: If opponent_id is invalid

    Example:
        >>> choose_parity("R1M1", "P02")
        "even"
    """
    # Implementation
```

### 5. Logging

**Rule:** Use structured JSON logging everywhere.

**Setup:**
```python
from player_agent.utils.logger import logger

# Log events
logger.info("Game started", match_id="R1M1", opponent_id="P02")

# Log errors
logger.error("Failed to connect", error=str(e), exc_info=True)
```

**Output:**
```json
{"timestamp":"2025-12-20T10:00:00Z","level":"INFO","agent_id":"P01","message":"Game started","match_id":"R1M1"}
```

### 6. Folder Structure

**Rule:** Follow `docs/requirements/project-folder-structure-guide.md`.

**Key Locations:**
```
SHARED/
├── config/           # Configuration files
├── data/             # Runtime data (standings, matches)
└── logs/             # Structured logs

agents/
├── league_manager/   # League Manager agent
├── referee_REF01/    # Referee agent
└── player_P01/       # Player agent (YOUR CODE)
```

---

## 🛠️ Development Workflow

### Daily Workflow

1. **Activate venv:**
   ```bash
   source venv/bin/activate
   ```

2. **Write code** (remember: ≤150 lines per file)

3. **Add docstrings** to all functions

4. **Add logging** to all handlers

5. **Run tests:**
   ```bash
   pytest tests/
   ```

6. **Format code:**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   ```

7. **Validate standards:**
   ```bash
   python scripts/validate_standards.py agents/player_P01
   ```

8. **Commit if all checks pass**

### Before Committing Checklist

- [ ] All files ≤150 lines
- [ ] All functions have docstrings
- [ ] Logging used in all handlers
- [ ] Tests pass (`pytest`)
- [ ] Code formatted (`black`)
- [ ] Standards validation passes

---

## 📁 File Organization Examples

### Example 1: Player Agent

```
agents/player_P01/
├── venv/
├── requirements.txt
├── setup.py
├── src/
│   └── player_agent/
│       ├── __init__.py
│       ├── main.py              # Entry point (100 lines)
│       ├── config.py            # Configuration (80 lines)
│       │
│       ├── handlers/            # MCP tool handlers
│       │   ├── __init__.py
│       │   ├── invitation.py    # handle_game_invitation (60 lines)
│       │   ├── choice.py        # choose_parity (120 lines)
│       │   └── result.py        # notify_match_result (40 lines)
│       │
│       ├── strategies/          # Strategy implementations
│       │   ├── __init__.py
│       │   ├── base.py          # Strategy interface (50 lines)
│       │   ├── random_strategy.py    # Random (40 lines)
│       │   └── adaptive_strategy.py  # Adaptive (140 lines)
│       │
│       ├── storage/             # Data persistence
│       │   ├── __init__.py
│       │   ├── history.py       # Match history (100 lines)
│       │   └── profiler.py      # Opponent profiler (120 lines)
│       │
│       └── utils/               # Utilities
│           ├── __init__.py
│           ├── logger.py        # Logging setup (80 lines)
│           └── helpers.py       # Helper functions (60 lines)
│
└── tests/
    ├── conftest.py
    ├── unit/
    │   ├── test_strategies.py
    │   └── test_handlers.py
    └── integration/
        └── test_full_flow.py
```

### Example 2: Splitting Large File

**BEFORE (❌ 300 lines in one file):**
```
handlers.py (300 lines) - TOO LARGE!
```

**AFTER (✅ Split into 3 files):**
```
handlers/
├── __init__.py
├── invitation.py   (80 lines)  ✅
├── choice.py       (150 lines) ✅
└── result.py       (70 lines)  ✅
```

---

## 🧪 Testing

### Unit Tests

```python
# tests/unit/test_strategies.py

def test_random_strategy():
    """Test random strategy returns valid choice."""
    from player_agent.strategies.random_strategy import RandomStrategy

    strategy = RandomStrategy()
    choice = strategy.choose_parity("R1M1", "P02", [], {})

    assert choice in ["even", "odd"]
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_strategies.py::test_random_strategy
```

---

## 🔍 Validation

### Automatic Validation

```bash
# Validate your agent
python scripts/validate_standards.py agents/player_P01

# Output:
# ✅ Checking venv exists: PASS
# ✅ Checking requirements.txt: PASS
# ✅ Checking setup.py: PASS
# ✅ Validating file sizes: PASS
# ✅ Validating docstrings: PASS
# ✅ agents/player_P01 passes all standards
```

### Manual Checks

```bash
# Count lines in a file
grep -v '^\s*#' src/player_agent/main.py | grep -v '^\s*$' | wc -l

# Check for docstrings
head -20 src/player_agent/handlers/choice.py
# Should see """ at the top

# Check logging
grep -r "logger\." src/player_agent/
# Should see logger.info, logger.error, etc.
```

---

## 📚 Key Documents

1. **[implementation-standards.md](docs/standards/implementation-standards.md)** - Full standards (READ THIS!)
2. **[project-folder-structure-guide.md](docs/requirements/project-folder-structure-guide.md)** - Folder organization
3. **[player-agent-architecture.md](docs/architecture/player-agent-architecture.md)** - Player implementation guide
4. **[game-flow-design.md](docs/architecture/game-flow-design.md)** - Complete game flow
5. **[player-strategy-design.md](docs/architecture/player-strategy-design.md)** - Strategy algorithms

---

## ❓ Common Questions

### Q: Why separate venv for each agent?

**A:** Prevents dependency conflicts, allows different versions, easier testing and deployment.

### Q: Why 150 line limit?

**A:** Forces modular design, makes code easier to understand and test. If a file is too large, split it.

### Q: Do comments count toward the 150 line limit?

**A:** No. Only code lines count (excluding blank lines and comments).

### Q: What if I need a function with complex logic?

**A:** Break it into smaller helper functions in separate files. Example:
```python
# main_function.py (50 lines)
from .helpers import helper1, helper2, helper3

def main_function():
    result1 = helper1()
    result2 = helper2(result1)
    return helper3(result2)

# helpers.py (100 lines)
def helper1(): ...
def helper2(x): ...
def helper3(x): ...
```

### Q: How do I share code between agents?

**A:** Put shared code in `SHARED/league_sdk/` and install it:
```bash
cd SHARED/league_sdk
pip install -e .

# Then in your agent:
from league_sdk.config_loader import ConfigLoader
```

---

## 🚨 Common Mistakes to Avoid

### ❌ Mistake 1: No Virtual Environment
```bash
# WRONG: Installing globally
pip install fastapi

# RIGHT: Create and use venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### ❌ Mistake 2: Files Too Large
```python
# WRONG: handlers.py with 300 lines

# RIGHT: Split into multiple files
handlers/
├── invitation.py
├── choice.py
└── result.py
```

### ❌ Mistake 3: No Docstrings
```python
# WRONG: No docstring
def choose_parity(match_id, opponent_id):
    return "even"

# RIGHT: With docstring
def choose_parity(match_id: str, opponent_id: str) -> str:
    """Choose parity based on strategy.

    Args:
        match_id: Match identifier
        opponent_id: Opponent's ID

    Returns:
        "even" or "odd"
    """
    return "even"
```

### ❌ Mistake 4: No Logging
```python
# WRONG: No logging
def handle_invitation(params):
    return {"accept": True}

# RIGHT: With logging
def handle_invitation(params):
    logger.info("Invitation received", match_id=params["match_id"])
    return {"accept": True}
```

---

## ✅ Success Criteria

Your implementation is successful when:

1. ✅ `python scripts/validate_standards.py agents/player_P01` passes
2. ✅ `pytest` passes all tests
3. ✅ Agent starts without errors
4. ✅ Agent can register with League Manager
5. ✅ Agent can complete a full game
6. ✅ Logs are written to `SHARED/logs/agents/P01.log.jsonl`
7. ✅ All files ≤150 lines
8. ✅ All functions have docstrings

---

## 🎯 Next Steps

1. **Read full standards:** `docs/standards/implementation-standards.md`
2. **Generate agent template:** `python scripts/create_agent_template.py player P01`
3. **Setup venv and install:** Follow steps above
4. **Start coding:** Implement in `src/player_agent/`
5. **Test continuously:** `pytest` after each change
6. **Validate before commit:** `python scripts/validate_standards.py`

---

**Good luck! Follow the standards and your code will be maintainable, testable, and production-ready!** 🚀
