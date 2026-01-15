@echo off
REM ========================================
REM Auto Obsidian Environment Setup
REM Create virtual environment and install dependencies
REM ========================================

echo.
echo ========================================
echo Auto Obsidian Environment Setup
echo ========================================
echo.

REM Set environment name
set ENV_NAME=venv
set REQUIREMENTS=requirements.txt

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ first
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Creating virtual environment (%ENV_NAME%)...
if exist %ENV_NAME% (
    echo Virtual environment already exists, skipping
) else (
    python -m venv %ENV_NAME%
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
)

echo.
echo [3/5] Activating virtual environment...
call %ENV_NAME%\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)

echo.
echo [4/5] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [5/5] Installing dependencies...
echo This may take a few minutes, please wait...
echo.

pip install -r %REQUIREMENTS%
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    echo Please check your network or run manually: pip install -r %REQUIREMENTS%
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo Virtual environment location: %cd%\%ENV_NAME%
echo.
echo Usage:
echo   1. Activate: %ENV_NAME%\Scripts\activate.bat
echo   2. Run app:  python gui/main_window.py
echo   3. Build EXE: build_exe.bat
echo.
echo Next steps:
echo   - Edit config/config.yaml to configure API Key
echo   - Run: %ENV_NAME%\Scripts\activate.bat
echo   - Run: python gui/main_window.py
echo.

pause
