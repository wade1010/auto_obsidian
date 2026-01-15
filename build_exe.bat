@echo off
echo ========================================
echo Building AutoObsidian.exe
echo ========================================
echo.

call venv\Scripts\activate.bat

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller AutoObsidian.spec

echo.
echo ========================================
echo Build completed!
echo Output: dist\AutoObsidian.exe
echo ========================================
pause
