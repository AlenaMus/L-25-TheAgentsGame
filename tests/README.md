# System Integration Tests

This directory contains system-level integration tests that validate the complete tournament system with all agents (Player, Referee, League Manager) working together.

## Overview

Integration tests verify:
- **Task 26**: Player registration with League Manager
- **Task 27**: Referee registration with League Manager
- **Task 28**: Complete match flow (invitation → choice → result)
- **Task 29**: Round-robin scheduling
- **Task 30**: Standings calculation
- **Task 31**: Multi-player tournament (3+ players)
- **Task 32**: Full tournament execution
- **Task 33**: Performance testing (concurrent matches)
- **Task 34**: Timeout handling
- **Task 35**: Error recovery

## Prerequisites

Each agent must have its own virtual environment and dependencies installed:

```bash
# Install player agent dependencies
cd agents/player_agent
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -e .
deactivate

# Install referee agent dependencies
cd ../referee_agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
deactivate

# Install league manager dependencies
cd ../league_manager
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
deactivate
```

## Setup Integration Test Environment

Create a virtual environment for integration tests:

```bash
cd tests
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running Tests

### Run All Integration Tests

```bash
# From project root
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ -v --cov=agents --cov-report=html
```

### Run Specific Test Files

```bash
# Task 26: Player Registration
pytest tests/integration/test_player_registration.py -v

# Task 27: Referee Registration
pytest tests/integration/test_referee_registration.py -v

# Task 28: Match Flow
pytest tests/integration/test_match_flow.py -v

# Task 29: Scheduling
pytest tests/integration/test_scheduling.py -v

# Task 30: Standings
pytest tests/integration/test_standings.py -v

# Task 31-32: Tournament
pytest tests/integration/test_tournament.py -v

# Task 33: Performance
pytest tests/integration/test_performance.py -v

# Task 34: Timeouts
pytest tests/integration/test_timeouts.py -v

# Task 35: Error Recovery
pytest tests/integration/test_error_recovery.py -v
```

### Run Specific Test

```bash
pytest tests/integration/test_player_registration.py::test_player_registration_success -v
```

## Test Infrastructure

### Utilities

- **`AgentManager`**: Starts/stops agents in separate processes
- **`MCPClient`**: Makes HTTP JSON-RPC calls to agents
- **`PortManager`**: Allocates unique ports for test agents

### Fixtures

Provided by `tests/conftest.py`:

- **`agent_manager`**: Manages agent lifecycle
- **`league_manager`**: Starts League Manager agent
- **`referee`**: Starts Referee agent
- **`player`**: Starts single Player agent
- **`two_players`**: Starts two Player agents
- **`three_players`**: Starts three Player agents
- **`port_manager`**: Allocates unique ports

## How It Works

1. **Test Setup**: Fixtures start required agents on unique ports
2. **Test Execution**: Test makes HTTP JSON-RPC calls to agents
3. **Assertions**: Verify responses match expected protocol
4. **Cleanup**: Fixtures automatically stop agents after test

## Example Test Flow

```python
@pytest.mark.asyncio
async def test_player_registration_success(league_manager, player):
    """Test player can register with League Manager."""

    async with MCPClient() as client:
        # Send registration request
        response = await client.call_tool(
            endpoint=league_manager.endpoint,
            tool_name="register_player",
            params={
                "protocol": "league.v2",
                "message_type": "PLAYER_REGISTER_REQUEST",
                # ... other params
            }
        )

        # Verify response
        assert response["result"]["status"] == "ACCEPTED"
        assert "player_id" in response["result"]
```

## Debugging Failed Tests

### View Agent Logs

Agents write logs to `SHARED/logs/`:
- `SHARED/logs/agents/player_agent/P01.jsonl`
- `SHARED/logs/agents/referee_agent/REF01.jsonl`
- `SHARED/logs/league_manager/league_manager.jsonl`

### Run Tests with Debug Output

```bash
pytest tests/integration/test_player_registration.py -v -s
```

### Check Agent Process Output

If an agent crashes, check stderr:

```python
# In test, after agent crashes
print(agent.process.stderr.read())
```

## Common Issues

### Port Already in Use

```
OSError: [Errno 48] Address already in use
```

**Solution**: Kill any lingering agent processes:

```bash
# Find processes using ports 9000-9100
lsof -i :9000-9100  # Linux/Mac
netstat -ano | findstr "9000"  # Windows

# Kill the processes
kill -9 <PID>
```

### Agent Fails to Start

```
RuntimeError: Agent P01 failed to become ready within 30s
```

**Causes**:
- Agent code has syntax errors
- Agent dependencies not installed
- Agent crashed during startup

**Solution**:
1. Check agent logs in `SHARED/logs/`
2. Manually start the agent to see errors:
   ```bash
   cd agents/player_agent
   source venv/bin/activate
   python -m player_agent.main
   ```

### Import Errors

```
ModuleNotFoundError: No module named 'player_agent'
```

**Solution**: Install agent as package:
```bash
cd agents/player_agent
source venv/bin/activate
pip install -e .
```

## Test Development Guidelines

1. **Use fixtures**: Don't manually start/stop agents
2. **Async tests**: Mark with `@pytest.mark.asyncio`
3. **Use MCPClient**: Don't make raw HTTP requests
4. **Clean up**: Fixtures handle cleanup automatically
5. **Descriptive names**: Test names should explain what they test
6. **Document scenarios**: Use docstrings to explain test flow

## Next Steps

After Tasks 26-27 (registration tests) pass:

1. **Task 28**: Implement match flow integration tests
2. **Task 29**: Test scheduling algorithm
3. **Task 30**: Test standings calculation
4. **Task 31-32**: Test full tournament
5. **Task 33-35**: Test robustness (performance, timeouts, errors)

## Success Criteria

Phase 4 complete when:
- ✅ All registration tests pass (Tasks 26-27)
- ✅ Match flow tests pass (Task 28)
- ✅ Scheduling tests pass (Task 29)
- ✅ Standings tests pass (Task 30)
- ✅ Tournament tests pass (Tasks 31-32)
- ✅ Robustness tests pass (Tasks 33-35)
- ✅ No agent crashes during tests
- ✅ All timeouts enforced correctly
- ✅ Data persists correctly
