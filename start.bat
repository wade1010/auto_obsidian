@echo off
REM Auto Obsidian Launcher

echo ========================================
echo Starting Auto Obsidian...
echo ========================================
echo.

REM Check virtual environment
if not exist venv (
    echo [ERROR] Virtual environment not found
    echo Please run: python -m venv venv
    echo Then: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate and run
call venv\Scripts\activate.bat
python gui/main_window.py

REM Pause on error
if errorlevel 1 (
    echo.
    echo [ERROR] Program failed to run
    pause
)
