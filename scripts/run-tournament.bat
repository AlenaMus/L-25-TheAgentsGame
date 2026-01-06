@echo off
REM =================================================================
REM Complete Automated Tournament System with Game Orchestrator
REM =================================================================

echo.
echo ================================================================
echo    Even/Odd Game Tournament - Automated System
echo ================================================================
echo.
echo This script will:
echo   1. Start the Game Orchestrator with Integrated Dashboard
echo   2. Orchestrator will automatically:
echo      - Start League Manager
echo      - Start 2 Referees (auto-register)
echo      - Start 4 Players (auto-register)
echo      - Wait for all registrations
echo      - Start the tournament automatically
echo      - Monitor and display progress
echo      - Serve web dashboard with real-time updates
echo      - Show final results
echo.
echo ================================================================
echo.

REM Create required directories
echo Creating required directories...
if not exist "SHARED\logs\league" mkdir "SHARED\logs\league"
if not exist "SHARED\logs\referees" mkdir "SHARED\logs\referees"
if not exist "SHARED\logs\players" mkdir "SHARED\logs\players"
if not exist "SHARED\logs\orchestrator" mkdir "SHARED\logs\orchestrator"
if not exist "SHARED\data\leagues" mkdir "SHARED\data\leagues"
if not exist "SHARED\data\matches" mkdir "SHARED\data\matches"
if not exist "SHARED\data\players" mkdir "SHARED\data\players"
echo.

REM Check if orchestrator venv exists
if not exist "agents\game_orchestrator\venv\Scripts\python.exe" (
    echo ERROR: Game Orchestrator virtual environment not found!
    echo Please run: cd agents\game_orchestrator ^&^& python -m venv venv
    echo Then: venv\Scripts\activate ^&^& pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting Game Orchestrator...
echo.

REM Start Game Orchestrator (this will start all agents automatically)
echo Starting Game Orchestrator with Integrated Dashboard...
echo   - This will automatically start all agents and run the tournament
echo   - Integrated dashboard serves both WebSocket and REST API
echo.
agents\game_orchestrator\venv\Scripts\python.exe -m orchestrator.main --config agents/game_orchestrator/config/agents.json
