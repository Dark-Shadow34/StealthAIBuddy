@echo off
title StealthAI Buddy
echo Starting StealthAI Buddy...
python "%~dp0main.py"
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred. Press any key to exit.
    pause >nul
)
