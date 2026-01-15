@echo off
REM ========================================
REM 更新依赖包脚本
REM ========================================

set ENV_NAME=venv

echo.
echo ========================================
echo 更新 Auto Obsidian 依赖包
echo ========================================
echo.

REM 检查虚拟环境
if not exist %ENV_NAME% (
    echo [错误] 虚拟环境不存在
    echo 请先运行 setup_env.bat
    pause
    exit /b 1
)

REM 激活环境
call %ENV_NAME%\Scripts\activate.bat

REM 更新 pip
echo [1/2] 升级 pip...
python -m pip install --upgrade pip

echo.
echo [2/2] 更新依赖包...
pip install --upgrade -r requirements.txt

echo.
echo ========================================
echo 依赖更新完成！
echo ========================================
echo.

pause
