@echo off
REM ========================================
REM Update Dependencies Script
REM ========================================

set ENV_NAME=venv

echo.
echo ========================================
echo Update Auto Obsidian Dependencies
echo ========================================
echo.

REM Check virtual environment
if not exist %ENV_NAME% (
    echo [ERROR] Virtual environment not found
    echo Please run setup_env.bat first
    pause
    exit /b 1
)

REM Activate environment
call %ENV_NAME%\Scripts\activate.bat

REM Update pip
echo [1/2] Upgrading pip...
python -m pip install --upgrade pip

echo.
echo [2/2] Updating dependencies...
pip install --upgrade -r requirements.txt

echo.
echo ========================================
echo Dependencies updated successfully!
echo ========================================
echo.

pause
