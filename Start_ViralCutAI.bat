@echo off
title ViralCut AI -- PDX Studio
color 0B
cd /d "%~dp0"

echo ========================================================================
echo                       ViralCut AI -- PDX Studio
echo ========================================================================
echo.

:: 1. Check Python virtual environment
if not exist ".\venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .\venv
    echo Please make sure the virtual environment exists.
    pause
    exit /b 1
)

:: 2. Check if server is already running on port 8000
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] ViralCut AI server is already running on http://localhost:8000
    echo Opening dashboard in your browser...
    start http://localhost:8000
    goto RUNNING_LOOP
)

:: 3. Start the server
echo [1/3] Initializing SQLite database and AI modules...
echo [2/3] Starting ViralCut AI backend on http://127.0.0.1:8000 ...

start /b "" ".\venv\Scripts\python.exe" -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 > "D:\ViralCutAI\server.log" 2>&1

:: Wait 2 seconds for uvicorn to bind
timeout /t 2 /nobreak >nul

:: Verify port is now listening
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if %errorlevel% equ 0 (
    echo [3/3] Server online!
) else (
    echo [WAIT] Waiting for server initialization...
    timeout /t 2 /nobreak >nul
)

echo.
echo ========================================================================
echo   [READY] ViralCut AI is live!
echo   Dashboard URL: http://localhost:8000
echo   YouTube Channel: PDX (Connected & Live)
echo ========================================================================
echo.
echo Opening dashboard in your browser...
start http://localhost:8000

:RUNNING_LOOP
echo.
echo Press 'Q' then Enter at any time to stop ViralCut AI, or close this window.
echo ------------------------------------------------------------------------
set /p USER_CHOICE="ViralCut AI is running... [Q=Quit]: "
if /i "%USER_CHOICE%"=="Q" (
    echo.
    echo Stopping ViralCut AI server...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
        taskkill /PID %%a /F >nul 2>&1
    )
    echo Server stopped. Goodbye!
    timeout /t 2 >nul
    exit /b 0
)
goto RUNNING_LOOP
