@echo off
REM Auto Obsidian 打包脚本

echo ========================================
echo Auto Obsidian 打包工具
echo ========================================
echo.

REM 检查PyInstaller是否安装
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller未安装，正在安装...
    pip install pyinstaller
)

echo.
echo 开始打包...
echo.

REM 执行打包
pyinstaller build_spec.py

if errorlevel 1 (
    echo.
    echo 打包失败！
    pause
    exit /b 1
)

echo.
echo ========================================
echo 打包完成！
echo 可执行文件位置: dist\AutoObsidian.exe
echo ========================================
echo.

pause
