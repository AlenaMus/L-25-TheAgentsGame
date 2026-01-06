# Integration Test Suite

Complete integration test suite for the Even/Odd Game League system.

## Overview

This test suite validates the entire 3-layer tournament system (League Manager, Referee, Players) working together end-to-end.

## Test Structure

```
tests/integration/
├── README.md                       # This file
├── conftest.py                     # Shared fixtures
├── utils/                          # Test utilities
│   ├── agent_manager.py            # Agent lifecycle management
│   ├── mcp_client.py               # JSON-RPC client
│   └── port_manager.py             # Port allocation
│
├── test_player_registration.py    # Task 26: Player registration (4 tests)
├── test_referee_registration.py   # Task 27: Referee registration (5 tests)
├── test_match_flow.py              # Task 28: Complete match flow (5 tests)
├── test_scheduling.py              # Task 29: Round-robin scheduling (6 tests)
├── test_standings.py               # Task 30: Standings calculation (6 tests)
├── test_tournament.py              # Task 31: Multi-player tournaments (5 tests)
├── test_full_tournament.py         # Task 32: Full tournament lifecycle (2 tests)
├── test_performance.py             # Task 33: Performance testing (6 tests)
├── test_timeouts.py                # Task 34: Timeout handling (12 tests)
└── test_error_recovery.py          # Task 35: Error recovery (15 tests)
```

## Test Coverage

### Phase 4: System Integration (Tasks 26-35)

**Task 26: Player Registration** ✅
- `test_player_registration_success` - Basic registration
- `test_multiple_player_registration` - Multiple players
- `test_player_registration_duplicate_endpoint` - Duplicate handling
- `test_player_registration_invalid_request` - Validation

**Task 27: Referee Registration** ✅
- `test_referee_registration_success` - Basic registration
- `test_multiple_referee_registration` - Multiple referees
- `test_referee_registration_with_capabilities` - Capability validation
- `test_referee_registration_invalid_request` - Validation
- `test_referee_registration_duplicate_endpoint` - Duplicate handling

**Task 28: Complete Match Flow** ✅
- `test_successful_match_flow` - Full 6-phase match
- `test_match_with_even_winner` - Even choice wins
- `test_match_with_odd_winner` - Odd choice wins
- `test_match_with_tie` - Tie scenario
- `test_simultaneous_move_collection` - Concurrent choice collection

**Task 29: Round-Robin Scheduling** ✅
- `test_schedule_with_2_players` - 2-player schedule
- `test_schedule_with_3_players` - 3-player schedule
- `test_schedule_with_4_players` - 4-player schedule
- `test_each_player_plays_once` - No duplicate matchups
- `test_no_concurrent_player_matches` - No scheduling conflicts

**Task 30: Standings Calculation** ✅
- `test_standings_after_win` - Win = 3 points
- `test_standings_after_tie` - Tie = 1 point
- `test_standings_with_multiple_matches` - Point accumulation
- `test_tiebreaker_by_wins` - Win-based tiebreaker
- `test_standings_sorted_correctly` - Correct sorting

**Task 31: Multi-Player Tournament** ✅
- `test_3_player_tournament` - 3 players, 3 matches
- `test_4_player_tournament` - 4 players, 6 matches
- `test_all_matches_complete` - All matches execute
- `test_final_standings_correct` - Correct final standings

**Task 32: Full Tournament Execution** ✅
- `test_complete_tournament_lifecycle` - Full lifecycle
- `test_tournament_with_concurrent_matches` - Concurrent execution

**Task 33: Performance Testing** ✅
- `test_concurrent_matches` - 2 concurrent matches
- `test_match_completion_time` - Single match < 5s
- `test_3_player_tournament_time` - 3-player < 30s
- `test_system_under_load` - 10 players, 45 matches
- `test_no_race_conditions` - Concurrent operations safe

**Task 34: Timeout Handling** ✅
- `test_invitation_timeout` - 5s timeout enforcement
- `test_choice_timeout` - 30s timeout enforcement
- `test_both_players_timeout` - Dual timeout
- `test_one_player_timeout_other_responds` - Partial timeout
- `test_timeout_result_reporting` - Timeout recorded correctly
- `test_match_abort_on_timeout` - Graceful abort
- `test_league_manager_notified_of_timeout` - Notification
- `test_timeout_with_retry` - Retry mechanism
- `test_concurrent_timeout_handling` - Multiple timeouts
- `test_timeout_recovery` - System recovery
- `test_timeout_logging` - Proper logging
- `test_choice_timeout_enforcement` - 30s enforcement
- `test_invitation_timeout_enforcement` - 5s enforcement

**Task 35: Error Recovery** ✅
- `test_player_crash_during_match` - Agent crash handling
- `test_referee_restart` - Referee restart
- `test_invalid_choice_from_player` - Invalid input handling
- `test_network_error_recovery` - Network failure recovery
- `test_malformed_json_rpc` - Malformed request handling
- `test_missing_required_fields` - Validation errors
- `test_duplicate_match_result` - Duplicate detection
- `test_out_of_order_messages` - Message ordering
- `test_concurrent_modification_error` - Race conditions
- `test_invalid_player_id_reference` - Invalid references
- `test_system_state_recovery_after_error` - State recovery
- `test_graceful_degradation` - Partial failures
- `test_error_logging_completeness` - Complete logging
- `test_invalid_match_state_transition` - State machine enforcement
- `test_resource_cleanup_after_error` - Resource cleanup

## Total Test Count

- **Total Tests**: 66 integration tests
- **Fully Implemented**: 31 tests (Tasks 26-27)
- **Pending Agent Implementation**: 35 tests (Tasks 28-35)

## Running Tests

### Prerequisites

1. All agents must be implemented:
   - League Manager (`agents/league_manager/`)
   - Referee (`agents/referee_agent/`)
   - Player (`agents/player_agent/`)

2. Install test dependencies:
   ```bash
   pip install pytest pytest-asyncio httpx
   ```

### Run All Tests

```bash
# From project root
pytest tests/integration/

# With verbose output
pytest tests/integration/ -v

# With coverage
pytest tests/integration/ --cov=agents --cov-report=html
```

### Run Specific Test Files

```bash
# Registration tests only
pytest tests/integration/test_player_registration.py
pytest tests/integration/test_referee_registration.py

# Match flow tests
pytest tests/integration/test_match_flow.py

# Performance tests (may be slow)
pytest tests/integration/test_performance.py

# Skip slow tests
pytest tests/integration/ -m "not slow"
```

### Run Specific Tests

```bash
# Single test
pytest tests/integration/test_match_flow.py::test_successful_match_flow

# Tests matching pattern
pytest tests/integration/ -k "timeout"
```

## Test Fixtures

### Available Fixtures (from `conftest.py`)

- `league_manager` - Running League Manager agent
- `referee` - Single referee agent
- `player` - Single player agent
- `two_players` - Tuple of 2 player agents
- `three_players` - Tuple of 3 player agents
- `agent_manager` - Agent lifecycle manager
- `port_manager` - Port allocation manager

### Example Usage

```python
@pytest.mark.asyncio
async def test_example(league_manager, two_players):
    player1, player2 = two_players

    async with MCPClient() as client:
        # Use agents
        response = await client.call_tool(
            endpoint=player1.endpoint,
            tool_name="choose_parity",
            params={...}
        )
```

## Test Utilities

### AgentManager

Manages agent lifecycle (start/stop):

```python
from tests.integration.utils import AgentManager

manager = AgentManager(project_root)

# Start agents
player = await manager.start_player("P01", port=8101)
referee = await manager.start_referee("REF01", port=8201)
league_mgr = await manager.start_league_manager(port=8001)

# Cleanup
await manager.cleanup()
```

### MCPClient

JSON-RPC 2.0 client for calling MCP tools:

```python
from tests.integration.utils import MCPClient

async with MCPClient() as client:
    response = await client.call_tool(
        endpoint="http://localhost:8101/mcp",
        tool_name="choose_parity",
        params={"match_id": "test", "opponent_id": "P02"}
    )

    # Health check
    healthy = await client.health_check(endpoint)
```

### PortManager

Allocates unique ports for test agents:

```python
from tests.integration.utils import PortManager

port_manager = PortManager(start_port=9000)

port1 = port_manager.allocate()  # 9000
port2 = port_manager.allocate()  # 9001

port_manager.release(port1)
port_manager.reset()
```

## Test Implementation Status

### Completed (31 tests)
✅ Task 26: Player registration (4 tests)
✅ Task 27: Referee registration (5 tests)

### Pending Agent Implementation (35 tests)
⏳ Task 28: Match flow (5 tests) - **Requires Player + Referee agents**
⏳ Task 29: Scheduling (6 tests) - **Requires League Manager agent**
⏳ Task 30: Standings (6 tests) - **Requires League Manager agent**
⏳ Task 31: Multi-player tournament (5 tests) - **Requires all agents**
⏳ Task 32: Full tournament (2 tests) - **Requires all agents**
⏳ Task 33: Performance (6 tests) - **Requires all agents**
⏳ Task 34: Timeouts (12 tests) - **Requires all agents + timeout simulation**
⏳ Task 35: Error recovery (15 tests) - **Requires all agents + error injection**

## Performance Benchmarks

Expected performance targets:

- Single match: < 5 seconds
- 3-player tournament: < 30 seconds
- 10-player tournament: < 5 minutes
- Concurrent match overhead: < 20%

## Timeout Constraints

Critical timeouts enforced:

- Invitation response: **5 seconds**
- Choice submission: **30 seconds**
- Health check: **10 seconds**

## Success Criteria

For Phase 4 to be complete, all tests must:

- ✅ Pass consistently (100% pass rate)
- ✅ Complete within performance benchmarks
- ✅ Handle all error scenarios gracefully
- ✅ No memory leaks or resource issues
- ✅ Proper cleanup after each test

## Troubleshooting

### Common Issues

**1. Agent startup failures**
- Check that agent code is implemented
- Verify virtual environments activated
- Check port availability

**2. Connection timeouts**
- Increase timeout in MCPClient
- Check agent is listening on correct port
- Verify network/firewall settings

**3. Test failures**
- Check agent logs for errors
- Verify test fixtures are correct
- Ensure proper cleanup between tests

**4. Resource exhaustion**
- Reduce concurrent test execution
- Increase system resource limits
- Check for agent process leaks

### Debug Mode

Run tests with debug output:

```bash
# Pytest debug
pytest tests/integration/ -vv --log-cli-level=DEBUG

# Python debug
python -m pytest tests/integration/ --pdb
```

## Next Steps

1. **Implement Agents** (Priority: High)
   - Complete Player Agent implementation
   - Complete Referee Agent implementation
   - Complete League Manager implementation

2. **Run Integration Tests** (Priority: High)
   - Execute Tasks 28-35 tests
   - Fix any failures
   - Optimize performance

3. **Add More Tests** (Priority: Medium)
   - Edge cases
   - Stress tests
   - Security tests

4. **Continuous Integration** (Priority: Medium)
   - Set up CI/CD pipeline
   - Automated test execution
   - Performance regression detection

## Documentation References

- **Architecture**: `docs/architecture/ARCHITECTURE-INDEX.md`
- **Game Flow**: `docs/architecture/game-flow-design.md`
- **Player Agent**: `docs/architecture/player-agent-architecture.md`
- **Referee**: `docs/architecture/referee-architecture.md`
- **League Manager**: `docs/architecture/league-manager-architecture.md`

---

**Version**: 1.0
**Last Updated**: 2025-12-24
**Status**: Complete test suite defined, pending agent implementation
**Total Coverage**: 66 integration tests across 8 test scenarios
