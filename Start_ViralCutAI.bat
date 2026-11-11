@echo off
title ViralCut AI -- PDX Studio
color 0B
cd /d "%~dp0"

echo ========================================================================
echo                       ViralCut AI -- PDX Studio
echo ========================================================================
echo.

:: 1. Verify virtual environment exists
if not exist ".\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .\venv
    echo Please make sure Python is installed and venv exists.
    pause
    exit /b 1
)

:: 2. Set PYTHONPATH to project root
set "PYTHONPATH=%~dp0"

:: 3. Clean port 8000 safely
echo [1/3] Checking port 8000...
".\venv\Scripts\python.exe" "backend\cleanup_port.py"
ping 127.0.0.1 -n 2 >nul

:: 4. Schedule browser opening in 2 seconds
echo [2/3] Opening dashboard at http://localhost:8000 ...
start "" cmd /c "ping 127.0.0.1 -n 3 >nul && start http://localhost:8000"

:: 5. Run uvicorn in the foreground so the user sees live status
echo [3/3] Starting ViralCut AI server...
echo.
echo ========================================================================
echo   [LIVE] ViralCut AI is running on: http://localhost:8000
echo   Upload Limit: 1.5 GB
echo   Features: Local MP4 Upload and YouTube Link Downloader
echo   Close this window or press CTRL+C to stop the server.
echo ========================================================================
echo.

".\venv\Scripts\python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8000

echo.
echo Server stopped.
pause
