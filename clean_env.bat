@echo off
REM ========================================
REM 清理虚拟环境脚本
REM 删除虚拟环境和缓存文件
REM ========================================

set ENV_NAME=venv

echo.
echo ========================================
echo 清理 Auto Obsidian 环境
echo ========================================
echo.

echo 警告: 此操作将删除虚拟环境和以下目录:
echo   - %ENV_NAME%/ (虚拟环境)
echo   - build/ (打包缓存)
echo   - dist/ (打包输出)
echo   - __pycache__/ (Python缓存)
echo   - *.spec (PyInstaller生成的spec文件)
echo.

set /p confirm="确定要清理吗? (y/n): "
if /i not "%confirm%"=="y" (
    echo 已取消
    pause
    exit /b 0
)

echo.
echo 正在清理...

REM 删除虚拟环境
if exist %ENV_NAME% (
    echo 删除虚拟环境: %ENV_NAME%
    rmdir /s /q %ENV_NAME%
)

REM 删除打包缓存
if exist build (
    echo 删除打包缓存: build
    rmdir /s /q build
)

REM 删除打包输出
if exist dist (
    echo 删除打包输出: dist
    rmdir /s /q dist
)

REM 删除spec文件
del /q *.spec 2>nul

REM 删除Python缓存
for /d /r %%d in (__pycache__) do @if exist "%%d" (
    echo 删除缓存: %%d
    rmdir /s /q "%%d"
)

echo.
echo ========================================
echo 清理完成！
echo.
echo 如需重新安装，请运行: setup_env.bat
echo ========================================
echo.

pause
