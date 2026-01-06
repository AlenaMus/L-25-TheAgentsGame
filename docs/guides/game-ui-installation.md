# Game UI Installation Guide

## Prerequisites

- Python 3.11 or higher
- Node.js 18+ (for frontend, optional for now)
- Running tournament system with data in `SHARED/` directory

## Backend Installation

### 1. Navigate to game_ui directory

```bash
cd C:\AIDevelopmentCourse\L-25-TheGame\game_ui
```

### 2. Activate virtual environment

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
pip install -e .
```

### 4. Configure environment

```bash
# Copy example env file
cp .env.example .env

# Edit .env and adjust paths if needed
# Default paths assume tournament system is in parent directory
```

### 5. Start the backend server

```bash
python start.py
```

The server will start on `http://localhost:9001`

- API Documentation: http://localhost:9001/docs
- WebSocket endpoint: ws://localhost:9001/ws

## Verify Installation

### Check API

```bash
# Test health endpoint
curl http://localhost:9001/health

# Get tournament info
curl http://localhost:9001/api/tournament/info

# Get standings
curl http://localhost:9001/api/standings

# Get matches
curl http://localhost:9001/api/matches
```

### Test WebSocket

Use the browser console or a WebSocket client:

```javascript
const ws = new WebSocket('ws://localhost:9001/ws');

ws.onopen = () => {
    console.log('Connected to Game UI backend');
};

ws.onmessage = (event) => {
    console.log('Received event:', JSON.parse(event.data));
};
```

## Troubleshooting

### Error: "Data path not found"

- Ensure `SHARED/` directory exists in parent folder
- Check `SHARED_DATA_PATH` in `.env` file
- Verify tournament system has created data files

### Error: "Module not found"

- Make sure you activated the virtual environment
- Run `pip install -r requirements.txt` again
- Try `pip install -e .` from backend directory

### Error: "Port 9001 already in use"

- Change `PORT` in `.env` file
- Or stop the process using port 9001

### No WebSocket events

- Ensure tournament system is running
- Check that matches are being played
- Verify `SHARED/logs/matches/` has `.jsonl` files
- Check backend console for log tailer messages

## Next Steps

- Frontend development (React application)
- Create visualizations for matches
- Add admin panel
- Deploy to production

## File Structure

```
game_ui/
├── venv/                  # Virtual environment
├── backend/
│   ├── src/
│   │   ├── main.py        # FastAPI app (144 lines)
│   │   ├── config.py      # Configuration (78 lines)
│   │   ├── api/           # API routes
│   │   │   ├── tournament.py (61 lines)
│   │   │   ├── standings.py (41 lines)
│   │   │   ├── matches.py (77 lines)
│   │   │   └── players.py (87 lines)
│   │   ├── models/        # Data models
│   │   │   ├── tournament.py (30 lines)
│   │   │   ├── player.py (39 lines)
│   │   │   └── match.py (56 lines)
│   │   ├── services/      # Business logic
│   │   │   ├── data_reader.py (92 lines)
│   │   │   └── log_tailer.py (106 lines)
│   │   └── utils/
│   │       └── logger.py (37 lines)
│   ├── requirements.txt
│   ├── setup.py
│   └── start.py
├── frontend/             # (To be implemented)
└── README.md
```

All backend files comply with the 150-line limit!
