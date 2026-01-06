# 🎮 Running Tournament with Live UI Dashboard

## Quick Start

### Step 1: Start the Tournament
Open a terminal and run:

```bash
cd C:\AIDevelopmentCourse\L-25-TheGame\agents\game_orchestrator
.\venv\Scripts\python.exe -m orchestrator.main
```

### Step 2: Open the Dashboard
Open your web browser and navigate to:

```
http://localhost:9000
```

**That's it!** You'll see the live dashboard with real-time updates.

---

## 🖥️ Dashboard Features

### What You'll See:

1. **Agent Health Status**
   - Real-time health monitoring
   - Green = Healthy, Red = Unhealthy
   - All agents (League Manager, Referees, Players)

2. **Tournament Standings**
   - Live leaderboard
   - Updates after each match
   - Shows: Rank, Player ID, Points, W-L-D record

3. **Real-Time Updates**
   - WebSocket connection (automatic refresh)
   - No need to reload the page
   - See changes as they happen

---

## 📊 Dashboard URL Endpoints

### Main Dashboard
```
http://localhost:9000
```

### API Endpoints (for developers)

**Get Current Standings:**
```
GET http://localhost:9000/api/standings
```

**Get Agent Health:**
```
GET http://localhost:9000/api/health
```

**Get Tournament Status:**
```
GET http://localhost:9000/api/status
```

---

## 🎯 What You'll See in Real-Time

### 1. Tournament Start (0-10 seconds)
```
Agent Status:
✅ league_manager: HEALTHY
✅ REF01: HEALTHY
✅ REF02: HEALTHY
✅ P01: HEALTHY
✅ P02: HEALTHY
✅ P03: HEALTHY
✅ P04: HEALTHY
```

### 2. First Matches (10-20 seconds)
```
Tournament Standings:
Rank | Player | Points | W-L-D
-----|--------|--------|------
  1  | P01    |   3    | 1-0-0
  2  | P02    |   0    | 0-1-0
```

### 3. Tournament Progress (20-90 seconds)
Standings update after each match:
```
Tournament Standings:
Rank | Player | Points | W-L-D
-----|--------|--------|------
  1  | P13    |   9    | 3-0-0  ← Perfect record!
  2  | P14    |   4    | 1-1-1
  3  | P15    |   4    | 1-1-1
  4  | P16    |   0    | 0-3-0
```

---

## 🔧 Advanced: Enhanced Dashboard

Want a fancier UI? You can create your own enhanced dashboard!

### Option 1: Create Enhanced HTML

1. Create directory:
```bash
mkdir C:\AIDevelopmentCourse\L-25-TheGame\agents\game_orchestrator\src\orchestrator\dashboard\static
```

2. Create `dashboard.html` with your custom design

3. The orchestrator will automatically use it instead of the fallback HTML

### Option 2: Build a React/Vue Frontend

1. Create frontend directory:
```bash
mkdir C:\AIDevelopmentCourse\L-25-TheGame\frontend
```

2. Create `index.html` that connects to WebSocket:
```javascript
const ws = new WebSocket('ws://localhost:9000/ws');

ws.onmessage = (event) => {
    const update = JSON.parse(event.data);
    // Handle: health, standings, matches, etc.
};
```

3. The orchestrator will serve it automatically

---

## 📱 WebSocket Message Format

### Messages You'll Receive:

**Health Update:**
```json
{
    "type": "health",
    "data": {
        "league_manager": "HEALTHY",
        "REF01": "HEALTHY",
        "P01": "HEALTHY"
    }
}
```

**Standings Update:**
```json
{
    "type": "standings",
    "data": [
        {
            "rank": 1,
            "player_id": "P13",
            "points": 9,
            "wins": 3,
            "losses": 0,
            "draws": 0
        }
    ]
}
```

**Match Update (if implemented):**
```json
{
    "type": "match",
    "data": {
        "match_id": "league_2025_even_odd_R1_M001",
        "player_A": "P01",
        "player_B": "P02",
        "status": "in_progress",
        "moves": {
            "P01": "even",
            "P02": "odd"
        },
        "result": "pending"
    }
}
```

---

## 🎨 Customizing the Dashboard

### Add Match-by-Match Details

Edit `agents/game_orchestrator/src/orchestrator/dashboard/fallback_html.py` to add more displays:

```javascript
ws.onmessage = (event) => {
    const update = JSON.parse(event.data);

    if (update.type === 'match_start') {
        displayMatchStart(update.data);
    } else if (update.type === 'match_complete') {
        displayMatchResult(update.data);
    }
};
```

### Add Live Match Feed

You can modify the tournament controller to broadcast match events:

```python
# In match execution
await self.dashboard.broadcast_update('match_start', {
    'match_id': match_id,
    'player_A': player_a_id,
    'player_B': player_b_id
})

# After match completion
await self.dashboard.broadcast_update('match_complete', {
    'match_id': match_id,
    'winner': winner_id,
    'drawn_number': number,
    'choices': choices
})
```

---

## 🚀 Running Long Tournaments

### Run Without Timeout (Manual Stop)

```bash
cd C:\AIDevelopmentCourse\L-25-TheGame\agents\game_orchestrator
.\venv\Scripts\python.exe -m orchestrator.main
```

**To stop:** Press `Ctrl+C` in the terminal

### Run with Specific Duration

```bash
# Run for 5 minutes (300 seconds)
timeout 300 .\venv\Scripts\python.exe -m orchestrator.main

# Run for 10 minutes (600 seconds)
timeout 600 .\venv\Scripts\python.exe -m orchestrator.main
```

---

## 📸 What You Can See

### Basic Dashboard (Built-in)
- ✅ Agent health indicators
- ✅ Live standings table
- ✅ Win-Loss-Draw records
- ✅ Real-time point updates
- ✅ Player rankings

### Future Enhancements (You Can Add)
- 🎯 Match-by-match timeline
- 📊 Charts and graphs (win rate over time)
- 🎮 Move visualization (even/odd choices)
- 📈 Strategy analysis
- 🏆 Championship bracket view
- 🎭 Player "avatars" or icons
- 🔔 Notifications for big moments

---

## 🛠️ Troubleshooting

### Dashboard Not Loading?

1. **Check if port 9000 is available:**
```bash
netstat -ano | findstr :9000
```

2. **Change dashboard port** (if needed):
Edit `agents/game_orchestrator/src/orchestrator/main.py`:
```python
self.dashboard = DashboardServer(
    port=8888,  # Change to any free port
    tournament_controller=self.tournament
)
```

Then access: `http://localhost:8888`

### WebSocket Not Connecting?

1. Check browser console (F12) for errors
2. Verify tournament is running
3. Try refreshing the page

### No Updates Appearing?

1. Ensure tournament has started (Stage 8)
2. Check that matches are running
3. Verify WebSocket connection in browser console

---

## 💡 Pro Tips

1. **Open dashboard BEFORE starting tournament** to see everything from the beginning

2. **Use split screen**: Terminal on left, Browser on right

3. **Browser console** (F12) shows all WebSocket messages for debugging

4. **Multiple tabs**: Open multiple browser tabs to test real-time sync

5. **Mobile friendly**: Open `http://YOUR_IP:9000` on your phone (same network)

---

## 🎉 Enjoy the Show!

The dashboard lets you watch your tournament unfold in real-time. You'll see:
- Agents coming online
- Matches starting and completing
- Standings updating live
- Champions emerging

**Have fun watching your AI agents compete!** 🏆

---

**Quick Start Reminder:**
1. `cd agents/game_orchestrator`
2. `.\venv\Scripts\python.exe -m orchestrator.main`
3. Open browser → `http://localhost:9000`
4. Watch the tournament live! 🎮
