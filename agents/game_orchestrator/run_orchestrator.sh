#!/bin/bash
# Game Orchestrator Startup Script for Linux/Mac

echo "========================================"
echo "Game Orchestrator - Even/Odd Tournament"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run: python -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
python -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Dependencies not installed!"
    echo "Please run: pip install -r requirements.txt"
    exit 1
fi

# Create log directories
mkdir -p ../../SHARED/logs/orchestrator

# Run orchestrator
echo ""
echo "Starting Game Orchestrator..."
echo "Dashboard will be available at: http://localhost:9000"
echo ""
echo "Press Ctrl+C to stop the orchestrator"
echo ""

python -m orchestrator.main --config config/agents.json
