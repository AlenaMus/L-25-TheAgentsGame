# Implementation Standards

**Document Type:** Mandatory Standards
**Version:** 1.0
**Last Updated:** 2025-12-20
**Status:** FINAL - MANDATORY FOR ALL IMPLEMENTATIONS
**Target Audience:** ALL Developers

---

## ⚠️ CRITICAL: MANDATORY REQUIREMENTS

**ALL code in this project MUST follow these standards. No exceptions.**

These standards ensure:
- ✅ Code quality and maintainability
- ✅ Consistent project structure
- ✅ Isolated environments for each agent
- ✅ Debuggability through logging
- ✅ Readability through small, focused modules

---

## Table of Contents

1. [Virtual Environment Requirements](#1-virtual-environment-requirements)
2. [Package Structure Requirements](#2-package-structure-requirements)
3. [Code File Size Limit](#3-code-file-size-limit)
4. [Documentation Requirements](#4-documentation-requirements)
5. [Logging Requirements](#5-logging-requirements)
6. [Project Organization](#6-project-organization)
7. [Validation Checklist](#7-validation-checklist)

---

## 1. Virtual Environment Requirements

### 1.1 Rule: Each Agent Has Its Own venv

**MANDATORY:** Every agent (League Manager, Referee, Player) MUST have its own isolated virtual environment.

**Why:**
- Prevents dependency conflicts
- Allows different Python versions if needed
- Isolation for testing
- Easier deployment

### 1.2 Directory Structure

```
L-25-TheGame/
├── agents/
│   ├── league_manager/
│   │   ├── venv/                    # Virtual environment (gitignored)
│   │   ├── requirements.txt         # MANDATORY
│   │   ├── setup.py                 # MANDATORY (for packaging)
│   │   ├── src/                     # Source code
│   │   └── tests/                   # Tests
│   │
│   ├── referee_REF01/
│   │   ├── venv/                    # Separate venv
│   │   ├── requirements.txt         # MANDATORY
│   │   ├── setup.py                 # MANDATORY
│   │   ├── src/
│   │   └── tests/
│   │
│   └── player_P01/
│       ├── venv/                    # Separate venv
│       ├── requirements.txt         # MANDATORY
│       ├── setup.py                 # MANDATORY
│       ├── src/
│       └── tests/
│
├── SHARED/
│   └── league_sdk/                  # Shared SDK (also has venv)
│       ├── venv/
│       ├── requirements.txt
│       ├── setup.py
│       └── src/
│
└── .gitignore                       # Ignore all venv/ directories
```

### 1.3 Creating Virtual Environments

**For each agent, run:**

```bash
# Navigate to agent directory
cd agents/player_P01

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install agent as package (editable mode)
pip install -e .
```

### 1.4 requirements.txt Template

**File:** `agents/player_P01/requirements.txt`

```txt
# Core MCP Server
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# HTTP Client
httpx==0.25.2

# Strategy & Analysis
numpy==1.26.2
scipy==1.11.4

# Logging
loguru==0.7.2

# Configuration
python-dotenv==1.0.0
pydantic-settings==2.1.0

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0

# Code Quality
black==23.12.0
ruff==0.1.8
mypy==1.7.1

# Local package (shared SDK)
# Install with: pip install -e ../../SHARED/league_sdk
# league-sdk @ file:///../../SHARED/league_sdk
```

### 1.5 setup.py Template

**File:** `agents/player_P01/setup.py`

```python
"""
Setup script for Player Agent P01.
Makes the agent installable as a package.
"""

from setuptools import setup, find_packages

setup(
    name="player-agent-p01",
    version="1.0.0",
    description="Player Agent for Even/Odd League Tournament",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.2",
        "numpy>=1.26.2",
        "scipy>=1.11.4",
        "loguru>=0.7.2",
        "python-dotenv>=1.0.0",
        "pydantic-settings>=2.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.7.1",
        ]
    },
    entry_points={
        "console_scripts": [
            "player-p01=player_agent.main:main",
        ]
    },
)
```

---

## 2. Package Structure Requirements

### 2.1 Rule: Proper Python Package Structure

**MANDATORY:** All agents and shared code MUST be organized as proper Python packages.

### 2.2 Agent Package Structure

```
agents/player_P01/
├── venv/                           # Virtual environment (gitignored)
├── requirements.txt                # Dependencies
├── setup.py                        # Package metadata
├── pyproject.toml                  # Build configuration (optional)
├── README.md                       # Agent documentation
├── .env.example                    # Environment variables template
│
├── src/                            # Source code
│   └── player_agent/               # Main package
│       ├── __init__.py             # Package initialization
│       ├── main.py                 # Entry point (≤150 lines)
│       ├── config.py               # Configuration (≤150 lines)
│       │
│       ├── handlers/               # MCP tool handlers
│       │   ├── __init__.py
│       │   ├── invitation.py       # handle_game_invitation (≤150 lines)
│       │   ├── choice.py           # choose_parity (≤150 lines)
│       │   └── result.py           # notify_match_result (≤150 lines)
│       │
│       ├── strategies/             # Strategy implementations
│       │   ├── __init__.py
│       │   ├── base.py             # Strategy interface (≤150 lines)
│       │   ├── random_strategy.py  # Random strategy (≤150 lines)
│       │   └── adaptive_strategy.py # Adaptive strategy (≤150 lines)
│       │
│       ├── storage/                # Data persistence
│       │   ├── __init__.py
│       │   ├── history.py          # Match history (≤150 lines)
│       │   └── profiler.py         # Opponent profiler (≤150 lines)
│       │
│       └── utils/                  # Utilities
│           ├── __init__.py
│           ├── logger.py           # Logging setup (≤150 lines)
│           └── helpers.py          # Helper functions (≤150 lines)
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── conftest.py                 # Pytest fixtures
    ├── unit/                       # Unit tests
    │   ├── test_strategies.py
    │   └── test_handlers.py
    └── integration/                # Integration tests
        └── test_full_flow.py
```

### 2.3 Shared SDK Package Structure

```
SHARED/league_sdk/
├── venv/                           # SDK development environment
├── requirements.txt                # SDK dependencies
├── setup.py                        # SDK package metadata
│
├── src/
│   └── league_sdk/                 # SDK package
│       ├── __init__.py
│       ├── config_loader.py        # Config loading (≤150 lines)
│       ├── repositories.py         # Data access (≤150 lines)
│       ├── logger.py               # Logging utilities (≤150 lines)
│       ├── mcp_client.py           # MCP client (≤150 lines)
│       └── message_builder.py      # Message construction (≤150 lines)
│
└── tests/
    └── test_sdk.py
```

### 2.4 __init__.py Requirements

**MANDATORY:** Every package MUST have `__init__.py` with version and exports.

**Example:** `src/player_agent/__init__.py`

```python
"""
Player Agent Package for Even/Odd League Tournament.

This package implements a player agent that participates in
the Even/Odd game tournament using the MCP protocol.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Export main classes/functions
from .main import main
from .config import Config

__all__ = [
    "main",
    "Config",
]
```

---

## 3. Code File Size Limit

### 3.1 Rule: Maximum 150 Lines Per File

**MANDATORY:** No code file shall exceed **150 lines** (excluding blank lines and comments).

**Why:**
- Forces modular design
- Easier to understand and test
- Single Responsibility Principle
- Reduces merge conflicts

### 3.2 Counting Lines

```bash
# Count lines excluding blanks and comments
# Linux/Mac
grep -v '^\s*#' filename.py | grep -v '^\s*$' | wc -l

# Windows (PowerShell)
(Get-Content filename.py | Where-Object {$_ -notmatch '^\s*#' -and $_ -notmatch '^\s*$'}).Count
```

### 3.3 Example: Splitting Large Files

**❌ BAD (300 lines in one file):**

```python
# handlers.py (300 lines - TOO LARGE)

async def handle_game_invitation(params):
    # 100 lines of code
    pass

async def choose_parity(params):
    # 100 lines of code
    pass

async def notify_match_result(params):
    # 100 lines of code
    pass
```

**✅ GOOD (3 files, each ≤150 lines):**

```
handlers/
├── __init__.py
├── invitation.py       # 80 lines
├── choice.py           # 120 lines
└── result.py           # 50 lines
```

### 3.4 File Organization Strategy

**If a file exceeds 150 lines:**

1. **Extract helper functions** to separate module
2. **Split by responsibility** (handlers, strategies, utilities)
3. **Create subpackages** for complex modules

**Example:**

```python
# Before: game_logic.py (200 lines)

# After: Split into multiple files
game_logic/
├── __init__.py
├── state_machine.py    # 80 lines
├── number_generator.py # 40 lines
└── evaluator.py        # 60 lines
```

---

## 4. Documentation Requirements

### 4.1 Rule: All Functions MUST Have Docstrings

**MANDATORY:** Every function, class, and method MUST have a docstring using Google style.

### 4.2 Docstring Template

```python
def choose_parity(
    match_id: str,
    opponent_id: str,
    opponent_history: List[Dict],
    standings: Dict
) -> str:
    """
    Choose parity based on adaptive strategy.

    Analyzes opponent's past choices to detect patterns using
    chi-squared test. If pattern detected, exploits it. Otherwise,
    falls back to random choice.

    Args:
        match_id: Unique match identifier for logging
        opponent_id: Opponent's player ID (e.g., "P02")
        opponent_history: List of past matches against this opponent.
            Each match contains:
                - match_id (str): Match identifier
                - opponent_choice (str): "even" or "odd"
                - drawn_number (int): Random number 1-10
                - won (bool): Whether we won that match
        standings: Current tournament standings.
            Contains:
                - wins (int): Total wins
                - losses (int): Total losses
                - draws (int): Total draws
                - points (int): Total points

    Returns:
        str: Either "even" or "odd"

    Raises:
        ValueError: If opponent_history contains invalid data

    Examples:
        >>> history = [
        ...     {"opponent_choice": "even", "drawn_number": 8, "won": True},
        ...     {"opponent_choice": "even", "drawn_number": 2, "won": True}
        ... ]
        >>> choose_parity("R1M1", "P02", history, {"wins": 2})
        "odd"  # Exploits opponent's bias toward "even"

    Note:
        Requires minimum 5 matches in opponent_history for
        pattern detection. Falls back to random if insufficient data.
    """
    # Implementation here
    pass
```

### 4.3 Class Docstrings

```python
class AdaptiveStrategy(Strategy):
    """
    Adaptive strategy with statistical pattern detection.

    This strategy analyzes opponent's choice history to detect
    non-random patterns using chi-squared test. When a pattern
    is detected with statistical significance (p < 0.05), it
    exploits the bias by choosing the opposite parity.

    Attributes:
        min_samples (int): Minimum matches required for analysis (default: 5)
        significance (float): Statistical significance level (default: 0.05)

    Example:
        >>> strategy = AdaptiveStrategy(min_samples=5, significance=0.05)
        >>> choice = strategy.choose_parity("R1M1", "P02", history, standings)
        >>> assert choice in ["even", "odd"]

    See Also:
        RandomStrategy: Baseline strategy (50/50 random)
        LLMStrategy: LLM-enhanced strategic reasoning
    """

    def __init__(self, min_samples: int = 5, significance: float = 0.05):
        """
        Initialize adaptive strategy.

        Args:
            min_samples: Minimum matches needed for pattern detection
            significance: P-value threshold for pattern detection
                (default 0.05 = 95% confidence)
        """
        self.min_samples = min_samples
        self.significance = significance
```

### 4.4 Module Docstrings

**MANDATORY:** Every file MUST have a module docstring.

```python
"""
Adaptive Strategy Implementation.

This module implements the adaptive pattern detection strategy
for the Even/Odd game. It uses statistical analysis to detect
opponent patterns and exploits them when found.

Classes:
    AdaptiveStrategy: Main strategy class implementing pattern detection

Functions:
    detect_pattern: Chi-squared test for non-randomness
    exploit_bias: Counter opponent's detected bias

Typical usage example:
    from strategies.adaptive_strategy import AdaptiveStrategy

    strategy = AdaptiveStrategy(min_samples=5)
    choice = strategy.choose_parity(match_id, opponent_id, history, standings)
"""

import random
from typing import List, Dict
from scipy.stats import chisquare

# Rest of module...
```

---

## 5. Logging Requirements

### 5.1 Rule: Structured Logging MUST Be Used

**MANDATORY:** All agents MUST use structured JSON logging (loguru or similar).

**Why:**
- Essential for debugging distributed systems
- Enables log aggregation and querying
- Provides audit trail
- Performance monitoring

### 5.2 Logger Setup (≤150 lines)

**File:** `src/player_agent/utils/logger.py`

```python
"""
Structured JSON logging for player agent.

Provides configured logger instance for all modules.
Logs to both console (for development) and file (for production).
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

def setup_logger(agent_id: str, log_dir: str = "SHARED/logs/agents") -> None:
    """
    Configure structured JSON logging.

    Args:
        agent_id: Agent identifier (e.g., "P01")
        log_dir: Directory for log files

    Example:
        >>> setup_logger("P01")
        >>> logger.info("Agent started", version="1.0.0")
        {"timestamp": "2025-12-20T10:00:00Z", "level": "INFO", "agent_id": "P01", ...}
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{agent_id}.log.jsonl"

    # Console handler (human-readable, development)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        level="DEBUG",
        colorize=True
    )

    # File handler (JSON Lines, production)
    logger.add(
        str(log_file),
        format=_json_formatter,
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="gz"
    )

    # Add agent_id to all logs
    logger.configure(extra={"agent_id": agent_id})

def _json_formatter(record: dict) -> str:
    """
    Format log record as JSON.

    Args:
        record: Loguru record dictionary

    Returns:
        JSON string with standard fields
    """
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": record["level"].name,
        "agent_id": record["extra"].get("agent_id", "UNKNOWN"),
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }

    # Add extra fields from logger.bind() or logger.contextualize()
    for key, value in record["extra"].items():
        if key != "agent_id":  # Already added
            log_entry[key] = value

    return json.dumps(log_entry)

# Export configured logger
__all__ = ["logger", "setup_logger"]
```

### 5.3 Using the Logger

**In every module:**

```python
from player_agent.utils.logger import logger

async def handle_game_invitation(params: dict) -> dict:
    """Handle game invitation from referee."""
    # Log invitation received
    logger.info(
        "Game invitation received",
        match_id=params["match_id"],
        opponent_id=params["opponent_id"],
        conversation_id=params["conversation_id"]
    )

    # Process invitation
    try:
        result = _process_invitation(params)

        # Log success
        logger.debug(
            "Invitation accepted",
            match_id=params["match_id"]
        )

        return result

    except Exception as e:
        # Log error with context
        logger.error(
            "Failed to process invitation",
            match_id=params["match_id"],
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True  # Include stack trace
        )
        raise
```

### 5.4 Log Output Example

**Console (development):**
```
2025-12-20 10:15:00 | INFO     | handlers.invitation:handle_game_invitation | Game invitation received
```

**File (production - JSON Lines):**
```json
{"timestamp":"2025-12-20T10:15:00.123Z","level":"INFO","agent_id":"P01","module":"handlers.invitation","function":"handle_game_invitation","line":45,"message":"Game invitation received","match_id":"R1M1","opponent_id":"P02","conversation_id":"convr1m1001"}
```

### 5.5 Log Levels

**Use appropriate log levels:**

| Level | When to Use | Example |
|-------|-------------|---------|
| DEBUG | Detailed diagnostic info | "Choice computed: even" |
| INFO | Important events | "Game invitation received" |
| WARNING | Recoverable issues | "Opponent choice pattern not detected" |
| ERROR | Errors requiring attention | "Failed to connect to referee" |
| CRITICAL | System failure | "Cannot start MCP server" |

---

## 6. Project Organization

### 6.1 Rule: Follow project-folder-structure-guide.md

**MANDATORY:** ALL code MUST be organized according to the folder structure defined in `docs/requirements/project-folder-structure-guide.md`.

### 6.2 Key Structure from Guide

```
L-25-TheGame/
├── SHARED/                         # Shared resources
│   ├── config/                     # Configuration files
│   │   ├── system.json
│   │   ├── leagues/
│   │   ├── games/
│   │   └── defaults/
│   │
│   ├── data/                       # Runtime data
│   │   ├── leagues/
│   │   ├── matches/
│   │   └── players/
│   │
│   ├── logs/                       # Structured logs
│   │   ├── league/
│   │   ├── agents/
│   │   └── system/
│   │
│   └── league_sdk/                 # Shared SDK
│       ├── venv/
│       ├── requirements.txt
│       ├── setup.py
│       └── src/
│
├── agents/                         # Agent implementations
│   ├── league_manager/
│   │   ├── venv/
│   │   ├── requirements.txt
│   │   ├── setup.py
│   │   ├── src/
│   │   │   └── league_manager/
│   │   │       ├── main.py         # ≤150 lines
│   │   │       ├── config.py       # ≤150 lines
│   │   │       ├── handlers/       # Each ≤150 lines
│   │   │       ├── scheduler/      # Each ≤150 lines
│   │   │       ├── standings/      # Each ≤150 lines
│   │   │       └── utils/          # Each ≤150 lines
│   │   └── tests/
│   │
│   ├── referee_REF01/
│   │   ├── venv/
│   │   ├── requirements.txt
│   │   ├── setup.py
│   │   ├── src/
│   │   │   └── referee/
│   │   │       ├── main.py         # ≤150 lines
│   │   │       ├── game_orchestrator.py  # ≤150 lines
│   │   │       ├── game_logic/     # Each ≤150 lines
│   │   │       └── utils/          # Each ≤150 lines
│   │   └── tests/
│   │
│   └── player_P01/
│       ├── venv/
│       ├── requirements.txt
│       ├── setup.py
│       ├── src/
│       │   └── player_agent/
│       │       ├── main.py         # ≤150 lines
│       │       ├── handlers/       # Each ≤150 lines
│       │       ├── strategies/     # Each ≤150 lines
│       │       └── storage/        # Each ≤150 lines
│       └── tests/
│
└── docs/                           # Documentation
    ├── architecture/
    ├── requirements/
    └── standards/                  # THIS FILE
```

### 6.3 File Placement Rules

**Configuration files:**
- System-wide: `SHARED/config/system.json`
- League-specific: `SHARED/config/leagues/{league_id}.json`
- Agent defaults: `SHARED/config/defaults/player.json`

**Runtime data:**
- Standings: `SHARED/data/leagues/{league_id}/standings.json`
- Match results: `SHARED/data/matches/{league_id}/{match_id}.json`
- Player history: `SHARED/data/players/{player_id}/match_history.json`

**Logs:**
- Agent logs: `SHARED/logs/agents/{agent_id}.log.jsonl`
- League logs: `SHARED/logs/league/{league_id}/league.log.jsonl`
- System logs: `SHARED/logs/system/orchestrator.log.jsonl`

---

## 7. Validation Checklist

### 7.1 Pre-Commit Checklist

**Before committing code, verify:**

- [ ] **venv exists** for agent/package
- [ ] **requirements.txt** is complete and up-to-date
- [ ] **setup.py** is present with correct metadata
- [ ] **All files ≤150 lines** (excluding blanks/comments)
- [ ] **All functions have docstrings** (Google style)
- [ ] **All modules have module docstrings**
- [ ] **Logging is used** in all handlers and critical functions
- [ ] **Folder structure** follows project-folder-structure-guide.md
- [ ] **Tests exist** for new code
- [ ] **Code passes linting** (black, ruff, mypy)

### 7.2 Automated Validation Script

**File:** `scripts/validate_standards.py`

```python
"""
Validate code against implementation standards.

Usage:
    python scripts/validate_standards.py agents/player_P01
"""

import sys
from pathlib import Path

def validate_file_size(file_path: Path) -> bool:
    """Check if file is ≤150 lines."""
    with open(file_path, 'r') as f:
        lines = [l for l in f if l.strip() and not l.strip().startswith('#')]
    if len(lines) > 150:
        print(f"❌ {file_path}: {len(lines)} lines (max 150)")
        return False
    return True

def validate_docstrings(file_path: Path) -> bool:
    """Check if file has module docstring."""
    with open(file_path, 'r') as f:
        content = f.read()
    if not content.strip().startswith('"""'):
        print(f"❌ {file_path}: Missing module docstring")
        return False
    return True

def validate_agent(agent_dir: Path) -> bool:
    """Validate entire agent directory."""
    success = True

    # Check venv exists
    if not (agent_dir / "venv").exists():
        print(f"❌ {agent_dir}: Missing venv/")
        success = False

    # Check requirements.txt exists
    if not (agent_dir / "requirements.txt").exists():
        print(f"❌ {agent_dir}: Missing requirements.txt")
        success = False

    # Check setup.py exists
    if not (agent_dir / "setup.py").exists():
        print(f"❌ {agent_dir}: Missing setup.py")
        success = False

    # Validate all Python files
    for py_file in agent_dir.rglob("*.py"):
        if "venv" in str(py_file):
            continue
        if not validate_file_size(py_file):
            success = False
        if not validate_docstrings(py_file):
            success = False

    return success

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python validate_standards.py <agent_dir>")
        sys.exit(1)

    agent_dir = Path(sys.argv[1])
    if not agent_dir.exists():
        print(f"Error: {agent_dir} does not exist")
        sys.exit(1)

    if validate_agent(agent_dir):
        print(f"✅ {agent_dir} passes all standards")
        sys.exit(0)
    else:
        print(f"❌ {agent_dir} fails standards validation")
        sys.exit(1)
```

**Usage:**

```bash
# Validate player agent
python scripts/validate_standards.py agents/player_P01

# Validate all agents
for agent in agents/*/; do
    python scripts/validate_standards.py "$agent"
done
```

### 7.3 CI/CD Integration

**Add to GitHub Actions or similar:**

```yaml
# .github/workflows/validate-standards.yml
name: Validate Implementation Standards

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Validate all agents
        run: |
          for agent in agents/*/; do
            python scripts/validate_standards.py "$agent" || exit 1
          done
```

---

## Summary

**MANDATORY Implementation Standards:**

1. ✅ **Virtual Environment:** Each agent has own venv
2. ✅ **Package Structure:** Proper setup.py and __init__.py
3. ✅ **File Size:** ≤150 lines per file
4. ✅ **Documentation:** All functions have docstrings
5. ✅ **Logging:** Structured JSON logging throughout
6. ✅ **Organization:** Follow project-folder-structure-guide.md

**Enforcement:**
- Pre-commit validation script
- CI/CD checks
- Code review requirements
- Automated testing

**Non-Compliance:**
- Code will not be merged
- Pull requests will be rejected
- Builds will fail

---

**Related Documents:**
- [project-folder-structure-guide.md](../requirements/project-folder-structure-guide.md) - Folder organization
- All architecture documents in `docs/architecture/`

---

**Document Status:** FINAL - MANDATORY
**Last Updated:** 2025-12-20
**Version:** 1.0
**Enforcement:** IMMEDIATE
