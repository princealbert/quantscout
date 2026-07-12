@echo off
chcp 65001 >nul
title QuantScout - 策略控制器 (端口 8502)

REM ============================================================
REM QuantScout 量化选股系统 - 策略控制器启动脚本
REM 功能:
REM   1. 自动切换到脚本所在目录(项目根目录)
REM   2. 自动激活 conda dcquant 虚拟环境(若存在)
REM   3. 启动策略控制器 (端口 8502)
REM   4. 自动打开浏览器
REM ============================================================

cd /d "%~dp0"

echo ============================================================
echo  QuantScout 量化选股系统 - 策略控制器
echo ============================================================
echo  项目目录: %CD%
echo  访问地址: http://localhost:8502
echo  按 Ctrl+C 可停止服务器
echo ============================================================
echo.

REM ---- 尝试激活 conda dcquant 环境 ----
set "CONDA_ACTIVATED=0"

REM 方式1: 通过 conda hook 初始化(推荐,兼容性最好)
where conda >nul 2>nul
if %errorlevel%==0 (
    call conda activate dcquant >nul 2>nul
    if %errorlevel%==0 (
        set "CONDA_ACTIVATED=1"
        echo [OK] 已激活 conda 环境: dcquant
        echo.
    )
)

REM 方式2: 通过常见安装路径手动激活
if "%CONDA_ACTIVATED%"=="0" (
    set "CONDA_BASE="
    if exist "%USERPROFILE%\anaconda3\Scripts\conda.exe" set "CONDA_BASE=%USERPROFILE%\anaconda3"
    if exist "%USERPROFILE%\miniconda3\Scripts\conda.exe" set "CONDA_BASE=%USERPROFILE%\miniconda3"
    if exist "%USERPROFILE%\AppData\Local\anaconda3\Scripts\conda.exe" set "CONDA_BASE=%USERPROFILE%\AppData\Local\anaconda3"
    if exist "%USERPROFILE%\AppData\Local\miniconda3\Scripts\conda.exe" set "CONDA_BASE=%USERPROFILE%\AppData\Local\miniconda3"
    if exist "C:\ProgramData\anaconda3\Scripts\conda.exe" set "CONDA_BASE=C:\ProgramData\anaconda3"
    if exist "C:\ProgramData\miniconda3\Scripts\conda.exe" set "CONDA_BASE=C:\ProgramData\miniconda3"

    if defined CONDA_BASE (
        call "%CONDA_BASE%\Scripts\activate.bat" dcquant >nul 2>nul
        if %errorlevel%==0 (
            set "CONDA_ACTIVATED=1"
            echo [OK] 已激活 conda 环境: dcquant ^(路径: %CONDA_BASE%^)
            echo.
        )
    )
)

if "%CONDA_ACTIVATED%"=="0" (
    echo [WARN] 未能激活 conda dcquant 环境,将使用系统 Python
    echo [INFO] 如需使用 dcquant 环境,请先运行:
    echo        setup_wizard.py --auto-fix
    echo.
)

REM ---- 检查 Python 是否可用 ----
where python >nul 2>nul
if not %errorlevel%==0 (
    echo [FAIL] 未找到 Python,请先安装 Python 3.8+
    echo [LINK] 下载地址: https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM ---- 设置 UTF-8 编码环境变量 ----
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

REM ---- 启动策略控制器 ----
echo [INFO] 正在启动策略控制器...
echo [INFO] 浏览器将在 2 秒后自动打开 http://localhost:8502
echo.

REM 延迟 2 秒后打开浏览器(使用后台 PowerShell)
start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8502'"

REM 启动 Streamlit(前台运行,便于查看日志和 Ctrl+C 停止)
python -m streamlit run strategy_controller/main.py --server.port 8502 --server.headless true --server.address 127.0.0.1 --logger.level info --server.runOnSave false

if %errorlevel% neq 0 (
    echo.
    echo [FAIL] 策略控制器启动失败,错误码: %errorlevel%
    echo [INFO] 排查建议:
    echo        1. 运行 python setup_wizard.py --diagnose 查看诊断报告
    echo        2. 检查依赖是否完整: pip install -r requirements.txt
    echo        3. 确认东财掘金终端已启动
    echo.
)

echo.
echo ============================================================
echo  策略控制器已停止
echo ============================================================
pause
