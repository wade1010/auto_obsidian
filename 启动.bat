@echo off
REM Auto Obsidian 启动脚本

echo ========================================
echo Auto Obsidian 启动中...
echo ========================================
echo.

REM 检查虚拟环境
if not exist venv (
    echo [错误] 虚拟环境不存在
    echo 请先运行: python -m venv venv
    echo 然后: venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

REM 激活虚拟环境并运行
call venv\Scripts\activate.bat
python main.py

REM 如果出错，暂停查看
if errorlevel 1 (
    echo.
    echo [错误] 程序运行失败
    pause
)
