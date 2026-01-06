# How to Run the Complete Tournament System

**Last Updated:** 2025-12-28
**System Status:** ✅ Production Ready

---

## 🎯 Quick Start (Recommended)

**One-click automated tournament:**

```batch
RUN_COMPLETE_TOURNAMENT.bat
```

This will:
1. ✅ Start Game Orchestrator (which automatically starts all agents)
2. ✅ Start Game UI Backend for visualization
3. ✅ Run a complete tournament automatically
4. ✅ Display final results

**No manual configuration needed!**

---

## 📋 What Happens Automatically

When you run the script, the **Game Orchestrator** will:

### Stage 1-3: Agent Startup (Automatic)
```
[INFO] Starting League Manager on port 8000...
[INFO] League Manager ready
[INFO] Starting 2 referees...
[INFO] Starting 4 players...
```

### Stage 4-5: Registration (Automatic)
```
[INFO] Waiting for agent registrations...
[INFO] Referee REF01 registered successfully
[INFO] Referee REF02 registered successfully
[INFO] Player P01 registered successfully
[INFO] Player P02 registered successfully
[INFO] Player P03 registered successfully
[INFO] Player P04 registered successfully
[INFO] All 6 agents registered!
```

### Stage 6: Tournament Start (Automatic)
```
[INFO] Auto-starting tournament...
[INFO] Tournament started - Round 1 of 3
[INFO] 2 matches scheduled for round 1
```

### Stage 7-9: Tournament Execution (Automatic)
```
[INFO] Match P01 vs P02 - Result: P01 wins
[INFO] Match P03 vs P04 - Result: P04 wins
[INFO] Round 1 complete
[INFO] Current standings:
      1. P01 - 3 points (1-0-0)
      2. P04 - 3 points (1-0-0)
      3. P02 - 0 points (0-1-0)
      4. P03 - 0 points (0-1-0)
[INFO] Starting Round 2...
```

### Stage 10: Final Results (Automatic)
```
[INFO] Tournament complete!
[INFO] Final standings:
      1. P03 - 27 points (9-0-0) 🏆
      2. P01 - 18 points (6-3-0)
      3. P02 - 9 points (3-6-0)
      4. P04 - 0 points (0-9-0)
```

---

## 🖥️ System Architecture

```
┌─────────────────────────────────────────────────┐
│         Game Orchestrator (Master)              │
│         Port 9000 - Dashboard                   │
│                                                 │
│  Manages:                                       │
│  • Agent lifecycle (start/stop/restart)         │
│  • Health monitoring                            │
│  • Tournament execution                         │
│  • Progress tracking                            │
└─────────────────────────────────────────────────┘
                    ↓
    ┌───────────────────────────────────┐
    │                                   │
    ↓                                   ↓
┌─────────────────┐          ┌──────────────────┐
│ League Manager  │          │ Game UI Backend  │
│ Port 8000       │          │ Port 9001        │
│                 │          │                  │
│ • Registrations │          │ • Visualization  │
│ • Scheduling    │          │ • REST API       │
│ • Standings     │          │ • WebSocket      │
└─────────────────┘          └──────────────────┘
        ↓
    ┌───────────────────────────────────┐
    ↓                                   ↓
┌─────────────┐              ┌─────────────────┐
│  Referees   │              │    Players      │
│  • REF01    │              │    • P01        │
│  • REF02    │              │    • P02        │
│             │              │    • P03        │
│             │              │    • P04        │
└─────────────┘              └─────────────────┘
```

---

## 🌐 Access Points

After startup, you can access:

### Game Orchestrator Dashboard
**URL:** http://localhost:9000
**Features:**
- Agent health status (real-time)
- Tournament progress tracking
- System logs aggregation
- Error monitoring

### Game UI API & Docs
**URL:** http://localhost:9001/docs
**API Endpoints:**

```bash
# Get tournament info
GET http://localhost:9001/api/tournament

# Get live standings
GET http://localhost:9001/api/standings

# Get all matches
GET http://localhost:9001/api/matches

# Get live matches
GET http://localhost:9001/api/matches/live

# Get player statistics
GET http://localhost:9001/api/players/P01/stats
```

**WebSocket (Real-time Updates):**
```javascript
ws://localhost:9001/ws

// Events:
- match_started
- match_completed
- standings_updated
- round_started
- round_completed
- tournament_completed
```

---

## ⚙️ Configuration

The orchestrator is configured via `agents/game_orchestrator/config/agents.json`:

```json
{
  "orchestrator": {
    "dashboard_port": 9000,
    "health_check_interval": 5,
    "startup_grace_period": 2,
    "agent_startup_timeout": 30,
    "auto_start": true,              // Auto-start tournament
    "registration_timeout": 120,     // Max seconds to wait
    "min_players": 2,                // Minimum players required
    "min_referees": 1                // Minimum referees required
  }
}
```

**Key Settings:**
- `auto_start: true` - Tournament starts automatically when all agents register
- `registration_timeout: 120` - Max 2 minutes to wait for registrations
- `min_players: 2` - At least 2 players required to start
- `min_referees: 1` - At least 1 referee required to start

---

## 🔧 Manual Mode (Advanced)

If you want manual control over tournament start:

1. **Edit config:** Set `auto_start: false` in `config/agents.json`

2. **Start orchestrator:**
   ```batch
   cd agents\game_orchestrator
   venv\Scripts\activate
   python -m orchestrator.main --config config/agents.json
   ```

3. **Wait for registrations**, then manually start via API:
   ```bash
   curl -X POST http://localhost:8000/mcp \
     -H "Content-Type: application/json" \
     -d '{"method": "start_league", "params": {}}'
   ```

4. **Monitor via Dashboard:** http://localhost:9000

---

## 📊 Monitoring Tournament Progress

### Watch the Orchestrator Console

The Game Orchestrator window shows real-time progress:

```
[19:30:00] INFO Starting League Manager...
[19:30:02] INFO League Manager ready on port 8000
[19:30:02] INFO Starting 2 referees...
[19:30:04] INFO Starting 4 players...
[19:30:10] INFO All agents registered!
[19:30:10] INFO Auto-starting tournament...
[19:30:11] INFO Tournament started - Round 1 of 3
[19:30:15] INFO Match 1 complete: P01 wins
[19:30:20] INFO Match 2 complete: P03 wins
[19:30:21] INFO Round 1 complete
[19:30:21] INFO Current standings:
             1. P03 - 3 points (1-0-0)
             2. P01 - 3 points (1-0-0)
             ...
```

### Check Game UI API

Visit http://localhost:9001/docs and try:

- **GET /api/tournament** - Tournament status
- **GET /api/standings** - Current rankings
- **GET /api/matches** - All match results
- **GET /api/matches/live** - Currently running matches

### Use WebSocket for Real-time Updates

```javascript
const ws = new WebSocket('ws://localhost:9001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Tournament event:', data);

  if (data.event === 'match_completed') {
    console.log(`Match ${data.match_id} finished!`);
    console.log(`Winner: ${data.winner}`);
  }

  if (data.event === 'tournament_completed') {
    console.log('Tournament finished!');
    console.log('Final standings:', data.standings);
  }
};
```

---

## 🛑 Stopping the System

### Option 1: Close Orchestrator Window
Press `Ctrl+C` in the Game Orchestrator window. This will:
1. Stop monitoring
2. Gracefully shutdown all agents
3. Clean up resources

### Option 2: Kill Processes
```bash
# Windows
taskkill /F /FI "WINDOWTITLE eq Game Orchestrator*"
taskkill /F /FI "WINDOWTITLE eq Game UI*"

# Or just close the command windows
```

---

## 🐛 Troubleshooting

### Problem: Orchestrator won't start

**Check:**
```bash
cd agents\game_orchestrator
venv\Scripts\python.exe -c "import orchestrator; print('OK')"
```

**Fix:**
```bash
cd agents\game_orchestrator
venv\Scripts\pip.exe install -e .
```

### Problem: Agents fail to start

**Check logs:**
```bash
type SHARED\logs\orchestrator\startup.log
```

**Common issue:** Port already in use
```bash
# Check which ports are in use
netstat -an | findstr "8000 8001 8002 8101 8102 8103 8104"

# Kill processes on those ports if needed
```

### Problem: Registrations timeout

**Check config:**
- Ensure `registration_timeout` is long enough (default: 120s)
- Ensure agents are actually starting (check their windows)
- Verify network connectivity (all on localhost)

**Manual check:**
```bash
# Test League Manager is ready
curl http://localhost:8000/health

# Check registered agents
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "get_registrations", "params": {}}'
```

### Problem: Game UI shows no data

**Verify:**
1. Tournament has actually started
2. Data is being written to `SHARED/data/`
3. Game UI is reading from correct directory

**Check:**
```bash
# Verify data exists
dir SHARED\data\leagues\
dir SHARED\data\matches\

# Check Game UI config
type game_ui\backend\.env
```

---

## 📚 Additional Resources

**Documentation:**
- `docs/architecture/game-orchestrator-architecture.md` - Orchestrator design
- `docs/guides/game-orchestrator-runtime-guide.md` - Detailed runtime guide
- `docs/architecture/game-ui-architecture.md` - UI architecture
- `TASK_VERIFICATION_REPORT.md` - Complete system status

**Configuration:**
- `agents/game_orchestrator/config/agents.json` - Agent configuration
- `game_ui/backend/.env` - Game UI configuration
- `SHARED/config/` - Shared configuration files

**Logs:**
- `SHARED/logs/orchestrator/` - Orchestrator logs
- `SHARED/logs/league/` - League Manager logs
- `SHARED/logs/referees/` - Referee logs
- `SHARED/logs/players/` - Player logs
- `SHARED/logs/game_ui/` - Game UI logs

---

## ✨ Summary

**To run a complete automated tournament:**

1. **Double-click:** `RUN_COMPLETE_TOURNAMENT.bat`
2. **Watch:** Game Orchestrator window for progress
3. **Monitor:** http://localhost:9000 (Orchestrator Dashboard)
4. **Visualize:** http://localhost:9001/docs (Game UI API)
5. **Results:** Automatically displayed when tournament completes

**The system does everything for you!** 🎉

- ✅ Starts all agents in correct order
- ✅ Waits for automatic registrations
- ✅ Starts tournament automatically
- ✅ Monitors and displays progress
- ✅ Shows final results

**No manual intervention needed!**

---

**Questions or Issues?**
Check the logs in `SHARED/logs/` or review the documentation in `docs/`.
