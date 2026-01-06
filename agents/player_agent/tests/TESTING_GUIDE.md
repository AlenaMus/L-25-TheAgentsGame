# Quick Testing Guide for MCP Server

## Server Status

### Check if server is running
```bash
curl http://localhost:8101/health
```

Expected response:
```json
{
  "status": "healthy",
  "agent_id": "P01",
  "port": 8101,
  "tools": ["handle_game_invitation", "choose_parity", "notify_match_result"]
}
```

---

## Test All Endpoints

### 1. Initialize
```bash
curl -X POST http://localhost:8101/initialize \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {},
    "id": 1
  }'
```

### 2. Handle Game Invitation
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "handle_game_invitation",
    "params": {
      "protocol": "league.v2",
      "message_type": "GAME_INVITATION",
      "sender": "referee:REF01",
      "timestamp": "20250121T100000Z",
      "conversation_id": "test_conv_001",
      "auth_token": "test_token",
      "league_id": "league_2025_test",
      "round_id": 1,
      "match_id": "TEST_M1",
      "game_type": "even_odd",
      "role_in_match": "PLAYER_A",
      "opponent_id": "P02",
      "player_id": "P01"
    },
    "id": 100
  }'
```

### 3. Choose Parity
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "choose_parity",
    "params": {
      "protocol": "league.v2",
      "message_type": "CHOOSE_PARITY_CALL",
      "sender": "referee:REF01",
      "timestamp": "20250121T100500Z",
      "conversation_id": "test_conv_001",
      "auth_token": "test_token",
      "match_id": "TEST_M1",
      "player_id": "P01",
      "game_type": "even_odd",
      "context": {
        "opponent_id": "P02",
        "round_id": 1,
        "your_standings": {
          "wins": 0,
          "losses": 0,
          "draws": 0
        }
      },
      "deadline": "20250121T103000Z"
    },
    "id": 101
  }'
```

### 4. Notify Match Result
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "notify_match_result",
    "params": {
      "protocol": "league.v2",
      "message_type": "GAME_OVER",
      "sender": "referee:REF01",
      "timestamp": "20250121T101000Z",
      "conversation_id": "test_conv_001",
      "auth_token": "test_token",
      "match_id": "TEST_M1",
      "game_type": "even_odd",
      "player_id": "P01",
      "game_result": {
        "status": "WIN",
        "winner_player_id": "P01",
        "drawn_number": 8,
        "number_parity": "even",
        "choices": {
          "P01": "even",
          "P02": "odd"
        },
        "reason": "P01 chose even, number was 8 (even)"
      }
    },
    "id": 102
  }'
```

### 5. Test Error Handling (Invalid Method)
```bash
curl -X POST http://localhost:8101/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "nonexistent_method",
    "params": {},
    "id": 999
  }'
```

Expected error response:
```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found: nonexistent_method"
  },
  "id": 999
}
```

---

## Common Issues

### Server not running
```bash
# Check if port 8101 is in use
netstat -ano | grep ":8101"

# Start server
python -m player_agent.main
```

### Port already in use
```bash
# Find and kill process
netstat -ano | grep ":8101"
taskkill /F /PID <PID>
```

### View server logs
```bash
# Live logs (console output)
tail -f SHARED/logs/agents/P01.log.jsonl

# Or check the background process output
cat <output_file>
```

---

## Expected Responses

### Health Check
```json
{
  "status": "healthy",
  "agent_id": "P01",
  "port": 8101,
  "tools": ["handle_game_invitation", "choose_parity", "notify_match_result"]
}
```

### Initialize
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {"tools": {}},
    "serverInfo": {
      "name": "even-odd-agent-P01",
      "version": "1.0.0"
    }
  },
  "id": 1
}
```

### Handle Game Invitation
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "GAME_JOIN_ACK",
    "sender": "player:P01",
    "timestamp": "20251221T115301Z",
    "conversation_id": "test_conv_001",
    "auth_token": "tok_p01_temp",
    "match_id": "TEST_M1",
    "player_id": "P01",
    "arrival_timestamp": "20251221T115301Z",
    "accept": true
  },
  "id": 100
}
```

### Choose Parity
```json
{
  "jsonrpc": "2.0",
  "result": {
    "protocol": "league.v2",
    "message_type": "CHOOSE_PARITY_RESPONSE",
    "sender": "player:P01",
    "timestamp": "20251221T115312Z",
    "conversation_id": "test_conv_001",
    "auth_token": "tok_p01_temp",
    "match_id": "TEST_M1",
    "player_id": "P01",
    "parity_choice": "even"  # or "odd" (random)
  },
  "id": 101
}
```

### Notify Match Result
```json
{
  "jsonrpc": "2.0",
  "result": {
    "acknowledged": true
  },
  "id": 102
}
```

---

## Validation Checklist

- [ ] Health endpoint returns all three tools
- [ ] Initialize returns correct protocol version
- [ ] handle_game_invitation returns accept: true
- [ ] choose_parity returns "even" or "odd"
- [ ] notify_match_result returns acknowledged: true
- [ ] Invalid method returns error code -32601
- [ ] All responses follow JSON-RPC 2.0 format
- [ ] All responses include correct conversation_id
- [ ] All timestamps are in UTC format

---

## Performance Metrics

Expected response times:
- Health check: < 100ms
- Initialize: < 200ms
- handle_game_invitation: < 200ms (target: < 5s)
- choose_parity: < 500ms (target: < 30s)
- notify_match_result: < 100ms (no timeout)
