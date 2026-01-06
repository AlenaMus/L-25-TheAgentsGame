"""
Agent Template Generator.

Generates a complete agent directory structure following
implementation standards (venv, package structure, ≤150 lines, logging).

Usage:
    python scripts/create_agent_template.py player P01
    python scripts/create_agent_template.py referee REF01
    python scripts/create_agent_template.py league_manager
"""

import sys
import os
from pathlib import Path
from datetime import datetime

TEMPLATES = {
    "setup.py": '''"""
Setup script for {agent_name}.
Makes the agent installable as a package.
"""

from setuptools import setup, find_packages

setup(
    name="{package_name}",
    version="1.0.0",
    description="{description}",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(where="src"),
    package_dir={{"": "src"}},
    python_requires=">=3.11",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn[standard]>=0.24.0",
        "pydantic>=2.5.0",
        "httpx>=0.25.2",
        "loguru>=0.7.2",
        "python-dotenv>=1.0.0",
        "pydantic-settings>=2.1.0",
    ],
    extras_require={{
        "dev": [
            "pytest>=7.4.3",
            "pytest-asyncio>=0.21.1",
            "pytest-cov>=4.1.0",
            "black>=23.12.0",
            "ruff>=0.1.8",
            "mypy>=1.7.1",
        ]
    }},
    entry_points={{
        "console_scripts": [
            "{entry_point}={package_module}.main:main",
        ]
    }},
)
''',

    "requirements.txt": '''# Core MCP Server
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0

# HTTP Client
httpx==0.25.2

# Strategy & Analysis (for players)
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
''',

    "main.py": '''"""
{agent_name} - Main Entry Point.

This module initializes and starts the {agent_type} agent.
"""

import asyncio
from pathlib import Path

from {package_module}.utils.logger import logger, setup_logger
from {package_module}.config import Config

def main():
    """
    Main entry point for {agent_name}.

    Initializes configuration, sets up logging, and starts
    the MCP server.
    """
    # Load configuration
    config = Config()

    # Setup logging
    setup_logger(
        agent_id=config.agent_id or "{agent_id}",
        log_dir="SHARED/logs/agents"
    )

    logger.info(
        "{agent_name} starting",
        version="1.0.0",
        port=config.port
    )

    # TODO: Initialize MCP server
    # TODO: Register tools
    # TODO: Start server

    logger.info("{agent_name} started successfully")

if __name__ == "__main__":
    main()
''',

    "config.py": '''"""
Configuration management for {agent_name}.

Loads configuration from environment variables and config files.
"""

from pydantic_settings import BaseSettings
from typing import Optional

class Config(BaseSettings):
    """
    Configuration for {agent_name}.

    Attributes:
        agent_id: Agent identifier (e.g., "{agent_id}")
        port: HTTP server port
        league_manager_url: League Manager endpoint
        auth_token: Authentication token (set after registration)
        league_id: League identifier (set after registration)

    Example:
        >>> config = Config()
        >>> print(config.port)
        {default_port}
    """

    # Agent identification
    agent_id: Optional[str] = "{agent_id}"
    temp_name: str = "{temp_name}"
    display_name: str = "{display_name}"

    # Network configuration
    port: int = {default_port}
    league_manager_url: str = "http://localhost:8000/mcp"

    # Credentials (set after registration)
    auth_token: Optional[str] = None
    league_id: Optional[str] = None

    class Config:
        env_file = ".env"
        env_prefix = "{env_prefix}_"

    def set_credentials(
        self,
        agent_id: str,
        auth_token: str,
        league_id: str
    ):
        """
        Store credentials received during registration.

        Args:
            agent_id: Assigned agent ID
            auth_token: Authentication token
            league_id: League identifier
        """
        self.agent_id = agent_id
        self.auth_token = auth_token
        self.league_id = league_id
''',

    "logger.py": '''"""
Structured JSON logging for {agent_name}.

Provides configured logger instance for all modules.
"""

import sys
import json
from datetime import datetime, timezone
from pathlib import Path
from loguru import logger as _logger

# Remove default handler
_logger.remove()

def setup_logger(agent_id: str, log_dir: str = "SHARED/logs/agents") -> None:
    """
    Configure structured JSON logging.

    Args:
        agent_id: Agent identifier (e.g., "{agent_id}")
        log_dir: Directory for log files

    Example:
        >>> setup_logger("{agent_id}")
        >>> logger.info("Agent started")
    """
    # Create log directory
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    log_file = Path(log_dir) / f"{{agent_id}}.log.jsonl"

    # Console handler (development)
    _logger.add(
        sys.stderr,
        format="<green>{{time:YYYY-MM-DD HH:mm:ss}}</green> | <level>{{level: <8}}</level> | <level>{{message}}</level>",
        level="DEBUG",
        colorize=True
    )

    # File handler (production - JSON Lines)
    _logger.add(
        str(log_file),
        format=_json_formatter,
        level="INFO",
        rotation="1 day",
        retention="30 days",
        compression="gz"
    )

    # Add agent_id to all logs
    _logger.configure(extra={{"agent_id": agent_id}})

def _json_formatter(record: dict) -> str:
    """Format log record as JSON."""
    log_entry = {{
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": record["level"].name,
        "agent_id": record["extra"].get("agent_id", "UNKNOWN"),
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
        "message": record["message"],
    }}

    # Add extra fields
    for key, value in record["extra"].items():
        if key != "agent_id":
            log_entry[key] = value

    return json.dumps(log_entry)

# Export logger
logger = _logger
__all__ = ["logger", "setup_logger"]
''',

    "README.md": '''# {agent_name}

{description}

## Setup

### 1. Create Virtual Environment

```bash
cd agents/{dir_name}
python -m venv venv

# Activate (Windows)
venv\\Scripts\\activate

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
python -m {package_module}.main
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
python scripts/validate_standards.py agents/{dir_name}
```

## Project Structure

```
{dir_name}/
├── venv/                 # Virtual environment
├── requirements.txt      # Dependencies
├── setup.py             # Package configuration
├── README.md            # This file
├── .env.example         # Environment template
├── src/
│   └── {package_module}/
│       ├── main.py      # Entry point
│       ├── config.py    # Configuration
│       └── utils/
│           └── logger.py # Logging
└── tests/
    └── conftest.py      # Test fixtures
```

## Standards Compliance

This agent follows **implementation-standards.md**:

- ✅ Isolated virtual environment
- ✅ Proper package structure
- ✅ Files ≤150 lines
- ✅ All functions documented
- ✅ Structured JSON logging
- ✅ Follows project folder structure

Created: {created_date}
''',

    ".env.example": '''# {agent_name} Configuration

# Agent identification
{env_prefix}_AGENT_ID={agent_id}
{env_prefix}_DISPLAY_NAME="{display_name}"

# Network
{env_prefix}_PORT={default_port}
{env_prefix}_LEAGUE_MANAGER_URL=http://localhost:8000/mcp

# Credentials (set after registration)
# {env_prefix}_AUTH_TOKEN=
# {env_prefix}_LEAGUE_ID=
''',

    "conftest.py": '''"""
Pytest configuration and fixtures for {agent_name}.
"""

import pytest
from pathlib import Path

@pytest.fixture
def agent_config():
    """Provide test configuration."""
    from {package_module}.config import Config
    return Config(
        agent_id="{agent_id}",
        port={default_port},
        league_manager_url="http://localhost:8000/mcp"
    )

@pytest.fixture
def logger():
    """Provide test logger."""
    from {package_module}.utils.logger import logger, setup_logger
    setup_logger("{agent_id}")
    return logger
''',

    ".gitignore": '''# Virtual environment
venv/
env/
ENV/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# Testing
.pytest_cache/
.coverage
htmlcov/

# Build
build/
dist/
*.egg-info/
''',
}

def create_agent(agent_type: str, agent_id: str):
    """
    Create complete agent directory structure.

    Args:
        agent_type: Type of agent ("player", "referee", "league_manager")
        agent_id: Agent identifier (e.g., "P01", "REF01")
    """
    # Determine agent details
    if agent_type == "player":
        dir_name = f"player_{agent_id}"
        package_module = "player_agent"
        package_name = f"player-agent-{agent_id.lower()}"
        agent_name = f"Player Agent {agent_id}"
        description = "Player Agent for Even/Odd League Tournament"
        default_port = 8100 + int(agent_id[1:]) if agent_id.startswith("P") else 8101
        temp_name = f"player_{agent_id.lower()}"
        display_name = f"Agent {agent_id}"
        env_prefix = "PLAYER"
        entry_point = f"player-{agent_id.lower()}"

    elif agent_type == "referee":
        dir_name = f"referee_{agent_id}"
        package_module = "referee"
        package_name = f"referee-{agent_id.lower()}"
        agent_name = f"Referee {agent_id}"
        description = "Referee (Game Orchestrator) for Even/Odd League"
        default_port = 8001 if agent_id == "REF01" else 8000 + int(agent_id[3:])
        temp_name = f"referee_{agent_id.lower()}"
        display_name = f"Referee {agent_id}"
        env_prefix = "REFEREE"
        entry_point = f"referee-{agent_id.lower()}"

    elif agent_type == "league_manager":
        dir_name = "league_manager"
        package_module = "league_manager"
        package_name = "league-manager"
        agent_name = "League Manager"
        description = "League Manager (Tournament Orchestrator)"
        default_port = 8000
        temp_name = "league_manager"
        display_name = "League Manager"
        env_prefix = "LEAGUE"
        agent_id = "league_manager"
        entry_point = "league-manager"

    else:
        raise ValueError(f"Unknown agent type: {agent_type}")

    # Create base directory
    base_dir = Path("agents") / dir_name
    base_dir.mkdir(parents=True, exist_ok=True)

    print(f"Creating {agent_name} in agents/{dir_name}/")

    # Create directory structure
    directories = [
        base_dir / "src" / package_module,
        base_dir / "src" / package_module / "utils",
        base_dir / "tests",
    ]

    if agent_type == "player":
        directories.extend([
            base_dir / "src" / package_module / "handlers",
            base_dir / "src" / package_module / "strategies",
            base_dir / "src" / package_module / "storage",
        ])
    elif agent_type == "referee":
        directories.extend([
            base_dir / "src" / package_module / "handlers",
            base_dir / "src" / package_module / "game_logic",
        ])
    elif agent_type == "league_manager":
        directories.extend([
            base_dir / "src" / package_module / "handlers",
            base_dir / "src" / package_module / "scheduler",
            base_dir / "src" / package_module / "standings",
            base_dir / "src" / package_module / "registry",
        ])

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        # Create __init__.py
        init_file = directory / "__init__.py"
        if not init_file.exists() and "src" in str(directory):
            init_file.write_text(f'"""{directory.name} package."""\n')

    # Template variables
    template_vars = {
        "agent_name": agent_name,
        "agent_type": agent_type,
        "agent_id": agent_id,
        "dir_name": dir_name,
        "package_module": package_module,
        "package_name": package_name,
        "description": description,
        "default_port": default_port,
        "temp_name": temp_name,
        "display_name": display_name,
        "env_prefix": env_prefix,
        "entry_point": entry_point,
        "created_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Create files from templates
    files = {
        base_dir / "setup.py": "setup.py",
        base_dir / "requirements.txt": "requirements.txt",
        base_dir / "README.md": "README.md",
        base_dir / ".env.example": ".env.example",
        base_dir / ".gitignore": ".gitignore",
        base_dir / "src" / package_module / "main.py": "main.py",
        base_dir / "src" / package_module / "config.py": "config.py",
        base_dir / "src" / package_module / "utils" / "logger.py": "logger.py",
        base_dir / "tests" / "conftest.py": "conftest.py",
    }

    for file_path, template_name in files.items():
        if not file_path.exists():
            content = TEMPLATES[template_name].format(**template_vars)
            file_path.write_text(content)
            print(f"  Created: {file_path.relative_to(base_dir)}")

    # Create setup instructions
    setup_script = base_dir / "setup.sh"
    setup_script.write_text(f"""#!/bin/bash
# Setup script for {agent_name}

echo "Setting up {agent_name}..."

# Create virtual environment
python -m venv venv

# Activate (use appropriate command for your OS)
# Windows: venv\\Scripts\\activate
# Linux/Mac: source venv/bin/activate

echo "Virtual environment created. Now run:"
echo "  source venv/bin/activate  # (Linux/Mac)"
echo "  venv\\\\Scripts\\\\activate     # (Windows)"
echo "  pip install -r requirements.txt"
echo "  pip install -e ."
""")
    setup_script.chmod(0o755)
    print(f"  Created: setup.sh")

    print(f"\n✅ {agent_name} template created successfully!")
    print(f"\nNext steps:")
    print(f"  1. cd agents/{dir_name}")
    print(f"  2. python -m venv venv")
    print(f"  3. source venv/bin/activate  # (or venv\\Scripts\\activate on Windows)")
    print(f"  4. pip install -r requirements.txt")
    print(f"  5. pip install -e .")
    print(f"  6. Start implementing in src/{package_module}/")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_agent_template.py <agent_type> [agent_id]")
        print("\nExamples:")
        print("  python create_agent_template.py player P01")
        print("  python create_agent_template.py referee REF01")
        print("  python create_agent_template.py league_manager")
        sys.exit(1)

    agent_type = sys.argv[1]
    agent_id = sys.argv[2] if len(sys.argv) > 2 else "league_manager"

    try:
        create_agent(agent_type, agent_id)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
