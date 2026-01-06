# Integration Tests - Quick Start Guide

## TL;DR - Run Tests Now

```bash
# 1. Setup test environment (one time)
cd C:\AIDevelopmentCourse\L-25-TheGame\tests
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 2. Verify setup works
python verify_setup.py

# 3. Run integration tests
pytest integration/test_player_registration.py -v
pytest integration/test_referee_registration.py -v
```

---

## Prerequisites (One-Time Setup)

Each agent must be installed as a Python package:

```bash
# Player Agent
cd C:\AIDevelopmentCourse\L-25-TheGame\agents\player_agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
deactivate

# Referee Agent
cd C:\AIDevelopmentCourse\L-25-TheGame\agents\referee_agent
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
deactivate

# League Manager
cd C:\AIDevelopmentCourse\L-25-TheGame\agents\league_manager
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
deactivate
```

---

## Test Environment Setup

```bash
cd C:\AIDevelopmentCourse\L-25-TheGame\tests
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

---

## Verify Everything Works

```bash
# Make sure test venv is activated
cd C:\AIDevelopmentCourse\L-25-TheGame\tests
venv\Scripts\activate

# Run verification script
python verify_setup.py
```

**Expected Output**: All 6 tests pass with ✓ marks

---

## Run Integration Tests

### All Tests
```bash
pytest integration/ -v
```

### Specific Test File
```bash
# Task 26: Player Registration
pytest integration/test_player_registration.py -v

# Task 27: Referee Registration
pytest integration/test_referee_registration.py -v
```

### Specific Test Function
```bash
pytest integration/test_player_registration.py::test_player_registration_success -v
```

### With Coverage
```bash
pytest integration/ -v --cov=agents --cov-report=html
# Open htmlcov/index.html to view coverage report
```

---

## Troubleshooting

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```

**Fix**: Kill processes using ports 9000-9100
```bash
# Windows
netstat -ano | findstr "9000"
taskkill /PID <PID> /F

# Linux/Mac
lsof -i :9000-9100
kill -9 <PID>
```

### Agent Fails to Start
```
RuntimeError: Agent P01 failed to become ready within 30s
```

**Debug**:
1. Try starting agent manually to see errors:
   ```bash
   cd agents/player_agent
   venv\Scripts\activate
   python -m player_agent.main
   ```

2. Check agent logs:
   ```bash
   type C:\AIDevelopmentCourse\L-25-TheGame\SHARED\logs\agents\player_agent\P01.jsonl
   ```

### Module Not Found
```
ModuleNotFoundError: No module named 'player_agent'
```

**Fix**: Install agent as package:
```bash
cd agents/player_agent
venv\Scripts\activate
pip install -e .
```

---

## What's Being Tested

### Task 26: Player Registration ✅
- Players can register with League Manager
- Receive unique player IDs (P01, P02, ...)
- Receive auth tokens and league ID
- Duplicate handling works

### Task 27: Referee Registration ✅
- Referees can register with League Manager
- Receive unique referee IDs (REF01, REF02, ...)
- Receive auth tokens and league ID
- Game types stored correctly

---

## Test Infrastructure

### Key Components

**AgentManager** - Starts/stops agents in subprocesses
```python
agent_manager = AgentManager()
player = await agent_manager.start_player("P01", 9001)
```

**MCPClient** - Makes JSON-RPC calls
```python
async with MCPClient() as client:
    response = await client.call_tool(endpoint, tool_name, params)
```

**Fixtures** - Automatic agent management
```python
@pytest.mark.asyncio
async def test_something(league_manager, player):
    # Agents already started and ready
    # Will be stopped automatically after test
```

---

## Next Steps

After Tasks 26-27 pass:

1. **Implement Task 28**: Match Flow Tests
   - Create `integration/test_match_flow.py`
   - Test complete match orchestration

2. **Implement Task 29**: Scheduling Tests
   - Create `integration/test_scheduling.py`
   - Test round-robin algorithm

3. **Implement Task 30**: Standings Tests
   - Create `integration/test_standings.py`
   - Test points calculation

4. **Continue** with Tasks 31-35

---

## File Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── requirements.txt               # Dependencies
├── verify_setup.py                # Quick verification
├── QUICK_START.md                 # This file
├── README.md                      # Full documentation
└── integration/
    ├── test_player_registration.py    # Task 26 ✅
    ├── test_referee_registration.py   # Task 27 ✅
    └── utils/
        ├── agent_manager.py           # Agent lifecycle
        ├── mcp_client.py              # HTTP client
        └── port_manager.py            # Port allocation
```

---

## Common Commands

```bash
# Activate test environment
cd C:\AIDevelopmentCourse\L-25-TheGame\tests
venv\Scripts\activate

# Run all tests
pytest integration/ -v

# Run specific test
pytest integration/test_player_registration.py::test_player_registration_success -v

# Run with output
pytest integration/ -v -s

# Run with coverage
pytest integration/ -v --cov=agents

# Verify setup
python verify_setup.py

# Deactivate
deactivate
```

---

## Getting Help

1. **Full Documentation**: Read `tests/README.md`
2. **Progress Tracker**: Check `tests/PHASE4_PROGRESS.md`
3. **Implementation Details**: See `tests/IMPLEMENTATION_SUMMARY.md`
4. **Verify Setup**: Run `python verify_setup.py`

---

**Quick Start Last Updated**: 2025-12-24
