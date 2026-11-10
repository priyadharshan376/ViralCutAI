@echo off
title Stop ViralCut AI
color 0C
cd /d "%~dp0"

echo Stopping ViralCut AI server on port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /PID %%a /F >nul 2>&1
    echo Terminated process %%a
)

echo ViralCut AI stopped successfully.
timeout /t 2 >nul
exit /b 0
