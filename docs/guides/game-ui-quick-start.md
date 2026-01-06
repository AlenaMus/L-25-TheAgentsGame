# Game UI - Quick Start Guide

## What is Game UI?

A **visualization layer** for the Even/Odd tournament system. It displays:
- Live tournament standings
- Match results and progress
- Player statistics
- Real-time updates via WebSocket

## Architecture

```
┌──────────────────────────────────────────────┐
│           Game UI Backend                     │
│         (FastAPI Server)                      │
│                                               │
│  Reads from:                                  │
│  - SHARED/data/leagues/*/standings.json       │
│  - SHARED/data/matches/*/*.json               │
│  - SHARED/logs/matches/*.jsonl (real-time)    │
│                                               │
│  Provides:                                    │
│  - REST API (http://localhost:9001/api/*)     │
│  - WebSocket (ws://localhost:9001/ws)         │
└──────────────────────────────────────────────┘
```

## Installation (2 minutes)

```bash
# 1. Navigate to game_ui directory
cd C:\AIDevelopmentCourse\L-25-TheGame\game_ui

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Install backend dependencies
cd backend
pip install -r requirements.txt
pip install -e .

# 4. Create .env file (optional - defaults work)
cp .env.example .env

# 5. Start backend server
python start.py
```

Server will start on: http://localhost:9001

## Testing

### 1. Check API Documentation

Open browser: http://localhost:9001/docs

Interactive API documentation with all endpoints.

### 2. Test Endpoints

```bash
# Health check
curl http://localhost:9001/health

# Get standings
curl http://localhost:9001/api/standings

# Get all matches
curl http://localhost:9001/api/matches

# Get live matches
curl http://localhost:9001/api/matches/live

# Get players
curl http://localhost:9001/api/players
```

### 3. Test WebSocket (Browser Console)

```javascript
const ws = new WebSocket('ws://localhost:9001/ws');

ws.onopen = () => console.log('Connected!');
ws.onmessage = (e) => console.log('Event:', JSON.parse(e.data));
```

## How It Works

### 1. Data Reading

Backend reads from existing tournament data:

```python
# From data_reader.py
standings = data_reader.get_standings("default")
# Reads: SHARED/data/leagues/default/standings.json

matches = data_reader.get_all_matches("default") 
# Reads: SHARED/data/matches/default/**/*.json
```

### 2. Real-time Events

Log tailer monitors match logs:

```python
# From log_tailer.py
log_tailer.start_watching("matches")
# Watches: SHARED/logs/matches/*.jsonl

# New events are broadcast to WebSocket clients
```

### 3. API Endpoints

REST API provides data access:

- `GET /api/tournament/info` - Tournament metadata
- `GET /api/standings` - Current standings
- `GET /api/matches` - All matches (with filters)
- `GET /api/matches/{match_id}` - Single match
- `GET /api/players` - All players
- `GET /api/players/{player_id}/stats` - Player statistics

### 4. WebSocket Events

Real-time event broadcasting:

```json
{
  "type": "match_event",
  "match_id": "R1M1",
  "event_type": "number_drawn",
  "data": {
    "drawn_number": 8,
    "number_parity": "even"
  }
}
```

## Code Structure

All files ≤150 lines:

```
backend/src/
├── main.py (144 lines)           # FastAPI app + WebSocket
├── config.py (78 lines)          # Configuration
├── api/
│   ├── tournament.py (61 lines)  # Tournament endpoints
│   ├── standings.py (41 lines)   # Standings endpoints
│   ├── matches.py (77 lines)     # Matches endpoints
│   └── players.py (87 lines)     # Players endpoints
├── models/
│   ├── tournament.py (30 lines)  # Tournament models
│   ├── player.py (39 lines)      # Player models
│   └── match.py (56 lines)       # Match models
├── services/
│   ├── data_reader.py (92 lines) # Read SHARED/data/
│   └── log_tailer.py (106 lines) # Monitor SHARED/logs/
└── utils/
    └── logger.py (37 lines)      # Structured logging
```

Total: ~850 lines of clean, modular code

## Next Steps

1. **Frontend Development**
   - React application to visualize data
   - Real-time standings table
   - Live match viewer
   - Player profiles

2. **Enhanced Features**
   - Match replay from log events
   - Advanced statistics
   - Admin panel
   - Historical data charts

3. **Deployment**
   - Docker container
   - NGINX reverse proxy
   - Production configuration

## Troubleshooting

**Issue**: No data returned from API

**Solution**: 
- Ensure tournament system has created data in SHARED/data/
- Check file paths in .env
- Verify SHARED/data/leagues/default/ exists

**Issue**: WebSocket not receiving events

**Solution**:
- Check SHARED/logs/matches/ has .jsonl files
- Verify matches are actively being played
- Check backend console for log tailer status

**Issue**: Import errors

**Solution**:
- Activate virtual environment
- Run `pip install -e .` from backend directory
- Check all __init__.py files exist

## Support

- See INSTALL.md for detailed installation
- See README.md for architecture overview
- Check backend/src/ for implementation code
- Run tests: `pytest backend/tests/`

---

**Ready to visualize the tournament!** 

Start the backend and open http://localhost:9001/docs
