@echo off
REM ========================================
REM Auto Obsidian Launcher
REM Activate virtual environment and run
REM ========================================

set ENV_NAME=venv

REM Check if virtual environment exists
if not exist %ENV_NAME% (
    echo [ERROR] Virtual environment not found
    echo Please run setup_env.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call %ENV_NAME%\Scripts\activate.bat

REM Run program
echo.
echo ========================================
echo Starting Auto Obsidian...
echo ========================================
echo.

python gui/main_window.py

REM Pause if error occurs
if errorlevel 1 (
    echo.
    echo [ERROR] Program failed to run
    pause
)
