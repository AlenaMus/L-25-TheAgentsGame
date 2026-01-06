# Unit Tests - Quick Reference

## Overview
Unit tests for all three MCP tool handlers. Achieves 100% code coverage.

## Test Files
- `test_invitation.py` - 13 tests for handle_game_invitation
- `test_choice.py` - 19 tests for choose_parity
- `test_result.py` - 18 tests for notify_match_result

**Total**: 50 tests, 100% coverage

## Quick Commands

### Run All Unit Tests
```bash
pytest tests/unit/ -v
```

### Run Specific Test File
```bash
pytest tests/unit/test_invitation.py -v
pytest tests/unit/test_choice.py -v
pytest tests/unit/test_result.py -v
```

### Run with Coverage
```bash
pytest tests/unit/ --cov=src/player_agent/handlers --cov-report=term
```

### Run with HTML Coverage Report
```bash
pytest tests/unit/ --cov=src/player_agent/handlers --cov-report=html
# Open htmlcov/index.html in browser
```

### Run Single Test
```bash
pytest tests/unit/test_choice.py::test_choose_parity_returns_valid_choice -v
```

### Run Tests Matching Pattern
```bash
pytest tests/unit/ -k "protocol" -v  # All tests with "protocol" in name
pytest tests/unit/ -k "logs" -v      # All tests with "logs" in name
```

## Expected Results

### All Tests Pass
```
============================= 50 passed in 0.18s ==============================
```

### Coverage Report
```
Name                                      Stmts   Miss  Cover
-------------------------------------------------------------
src\player_agent\handlers\invitation.py      10      0   100%
src\player_agent\handlers\choice.py          21      0   100%
src\player_agent\handlers\result.py          21      0   100%
-------------------------------------------------------------
TOTAL                                        56      0   100%
```

## Test Categories

### Protocol Compliance Tests
- League.v2 protocol format
- Message type correctness
- Sender format (player:P01)
- UTC timestamp validation

### Functionality Tests
- Valid input handling
- Response generation
- Strategy integration (RandomStrategy)
- Error handling and fallbacks

### Edge Case Tests
- Missing/empty parameters
- Invalid strategy output
- Minimal params handling
- Boundary conditions (all drawn numbers 1-10)

### Integration Tests (with mocks)
- Logger interaction
- Strategy instantiation and usage
- Parameter passing between components

## What Each File Tests

### test_invitation.py
Tests that `handle_game_invitation` handler:
1. Always accepts invitations
2. Returns proper GAME_JOIN_ACK response
3. Preserves conversation_id and match_id
4. Formats response per league.v2 protocol
5. Includes all required envelope fields
6. Logs received and accepted events

### test_choice.py
Tests that `choose_parity` handler:
1. Returns valid choice ("even" or "odd")
2. Uses RandomStrategy for decision
3. Passes correct params to strategy
4. Handles missing context gracefully
5. Validates and corrects invalid choices
6. Logs requests, choices, and errors
7. Produces 50/50 statistical distribution

### test_result.py
Tests that `notify_match_result` handler:
1. Returns acknowledgment
2. Handles WIN/LOSS/DRAW results
3. Extracts opponent_id from choices
4. Extracts player and opponent choices
5. Handles missing/empty game_result
6. Logs all match details
7. Supports multiple calls

## Common Issues & Solutions

### Issue: Tests fail with import errors
**Solution**: Ensure you're in the virtual environment
```bash
. venv/Scripts/activate  # Windows Git Bash
```

### Issue: Coverage shows less than 100%
**Solution**: Check if all code paths are tested. Our tests achieve 100%.

### Issue: Async tests fail
**Solution**: Ensure @pytest.mark.asyncio decorator is present

### Issue: Mock tests fail
**Solution**: Verify patch path matches actual import path

## Test Quality Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 50 |
| Code Coverage | 100% |
| Execution Time | ~0.18s |
| Passing Rate | 100% |
| Lines of Test Code | ~1,285 |

## Next Steps

After unit tests, proceed to:
1. Integration tests (tests/integration/)
2. Timeout testing
3. End-to-end testing with mock referee
4. Deployment testing

## Documentation

For detailed implementation information, see:
- `TASK_5_UNIT_TESTS_SUMMARY.md` - Complete implementation summary
- `tests/conftest.py` - pytest fixtures and configuration
- Individual test files - Docstrings explain each test
