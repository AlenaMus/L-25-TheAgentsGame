@echo off
REM Game Orchestrator Startup Script for Windows

echo ========================================
echo Game Orchestrator - Even/Odd Tournament
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if dependencies are installed
python -c "import fastapi" 2>NUL
if errorlevel 1 (
    echo ERROR: Dependencies not installed!
    echo Please run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Create log directories
if not exist "..\..\SHARED\logs\orchestrator" (
    mkdir "..\..\SHARED\logs\orchestrator"
)

REM Run orchestrator
echo.
echo Starting Game Orchestrator...
echo Dashboard will be available at: http://localhost:9000
echo.
echo Press Ctrl+C to stop the orchestrator
echo.

python -m orchestrator.main --config config/agents.json

pause
