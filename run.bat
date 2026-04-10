@echo off
title UtilityToolsV2 - Token Checker
color 0b
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/
    pause
    exit /b
)
if not exist "venv" (
    echo [*] Creating virtual environment...
    python -m venv venv
)
echo [*] Installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt --quiet
echo [*] Starting script...
python main.py
echo.
echo [*] Script execution finished.
pause