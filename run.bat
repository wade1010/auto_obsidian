@echo off
REM ========================================
REM Auto Obsidian 启动脚本
REM 自动激活虚拟环境并运行程序
REM ========================================

set ENV_NAME=venv

REM 检查虚拟环境是否存在
if not exist %ENV_NAME% (
    echo [错误] 虚拟环境不存在
    echo 请先运行 setup_env.bat 创建环境
    pause
    exit /b 1
)

REM 激活虚拟环境
call %ENV_NAME%\Scripts\activate.bat

REM 运行程序
echo.
echo ========================================
echo 启动 Auto Obsidian...
echo ========================================
echo.

python main.py

REM 如果程序出错，暂停以显示错误信息
if errorlevel 1 (
    echo.
    echo [错误] 程序运行失败
    pause
)
