@echo off
echo ========================================
echo Building AutoObsidian.exe
echo ========================================
echo.

call venv\Scripts\activate.bat

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --onefile --windowed --name="AutoObsidian" --add-data="config;config" --hidden-import=PyQt5 --hidden-import=PyQt5.QtWidgets --hidden-import=PyQt5.QtCore --hidden-import=PyQt5.QtGui --hidden-import=apscheduler.schedulers.qt --hidden-import=zhipuai --hidden-import=openai gui/main_window.py

echo.
echo ========================================
echo Build completed!
echo Output: dist\AutoObsidian.exe
echo ========================================
pause
