@echo off
REM ========================================
REM Auto Obsidian 环境设置脚本
REM 自动创建虚拟环境并安装依赖
REM ========================================

echo.
echo ========================================
echo Auto Obsidian 环境设置
echo ========================================
echo.

REM 设置环境名称
set ENV_NAME=venv
set REQUIREMENTS=requirements.txt

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] Python 未安装或不在 PATH 中
    echo 请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/5] 检测 Python 版本...
python --version

echo.
echo [2/5] 创建虚拟环境 (%ENV_NAME%)...
if exist %ENV_NAME% (
    echo 虚拟环境已存在，跳过创建
) else (
    python -m venv %ENV_NAME%
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo 虚拟环境创建成功
)

echo.
echo [3/5] 激活虚拟环境...
call %ENV_NAME%\Scripts\activate.bat
if errorlevel 1 (
    echo [错误] 激活虚拟环境失败
    pause
    exit /b 1
)

echo.
echo [4/5] 升级 pip...
python -m pip install --upgrade pip

echo.
echo [5/5] 安装依赖包...
echo 这可能需要几分钟，请耐心等待...
echo.

pip install -r %REQUIREMENTS%
if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败
    echo 请检查网络连接或手动运行: pip install -r %REQUIREMENTS%
    pause
    exit /b 1
)

echo.
echo ========================================
echo 环境设置完成！
echo ========================================
echo.
echo 虚拟环境位置: %cd%\%ENV_NAME%
echo.
echo 使用方法:
echo   1. 激活环境: %ENV_NAME%\Scripts\activate.bat
echo   2. 运行程序: python main.py
echo   3. 打包EXE:   build.bat
echo.
echo 下一步:
echo   - 编辑 config/config.yaml 配置 API Key
echo   - 运行: %ENV_NAME%\Scripts\activate.bat
echo   - 运行: python main.py
echo.

pause
