@echo off
REM ========================================
REM Clean Environment Script
REM Remove virtual environment and cache files
REM ========================================

set ENV_NAME=venv

echo.
echo ========================================
echo Clean Auto Obsidian Environment
echo ========================================
echo.

echo WARNING: This will delete the virtual environment and these directories:
echo   - %ENV_NAME%/ (virtual environment)
echo   - build/ (build cache)
echo   - dist/ (build output)
echo   - __pycache__/ (Python cache)
echo   - *.spec (PyInstaller generated spec files)
echo.

set /p confirm="Are you sure you want to clean? (y/n): "
if /i not "%confirm%"=="y" (
    echo Cancelled
    pause
    exit /b 0
)

echo.
echo Cleaning...

REM Remove virtual environment
if exist %ENV_NAME% (
    echo Removing virtual environment: %ENV_NAME%
    rmdir /s /q %ENV_NAME%
)

REM Remove build cache
if exist build (
    echo Removing build cache: build
    rmdir /s /q build
)

REM Remove build output
if exist dist (
    echo Removing build output: dist
    rmdir /s /q dist
)

REM Remove spec files
del /q *.spec 2>nul

REM Remove Python cache
for /d /r %%d in (__pycache__) do @if exist "%%d" (
    echo Removing cache: %%d
    rmdir /s /q "%%d"
)

echo.
echo ========================================
echo Cleanup completed!
echo.
echo To reinstall, run: setup_env.bat
echo ========================================
echo.

pause
