@echo off
chcp 65001 >nul
title QuantScout (Port 8501)

REM ============================================================
REM QuantScout Launcher
REM 1. Locate dcquant conda env Python
REM 2. Start Streamlit (Home.py) in foreground
REM 3. Open browser after 3 seconds
REM 4. Real-time logs shown in this terminal window
REM ============================================================

cd /d "%~dp0"

echo ============================================================
echo  QuantScout
echo ============================================================
echo  Project:  %CD%
echo  URL:      http://localhost:8501
echo  Press Ctrl+C to stop
echo  This window shows real-time logs. Do not close.
echo ============================================================
echo.

REM ---- Locate dcquant Python ----
set "PYTHON_CMD="

REM Try common conda install paths for dcquant env python
if exist "D:\ProgramData\miniconda3\envs\dcquant\python.exe" set "PYTHON_CMD=D:\ProgramData\miniconda3\envs\dcquant\python.exe"
if exist "C:\ProgramData\miniconda3\envs\dcquant\python.exe" set "PYTHON_CMD=C:\ProgramData\miniconda3\envs\dcquant\python.exe"
if exist "C:\ProgramData\anaconda3\envs\dcquant\python.exe" set "PYTHON_CMD=C:\ProgramData\anaconda3\envs\dcquant\python.exe"
if exist "D:\ProgramData\anaconda3\envs\dcquant\python.exe" set "PYTHON_CMD=D:\ProgramData\anaconda3\envs\dcquant\python.exe"
if exist "%USERPROFILE%\miniconda3\envs\dcquant\python.exe" set "PYTHON_CMD=%USERPROFILE%\miniconda3\envs\dcquant\python.exe"
if exist "%USERPROFILE%\anaconda3\envs\dcquant\python.exe" set "PYTHON_CMD=%USERPROFILE%\anaconda3\envs\dcquant\python.exe"
if exist "%USERPROFILE%\AppData\Local\miniconda3\envs\dcquant\python.exe" set "PYTHON_CMD=%USERPROFILE%\AppData\Local\miniconda3\envs\dcquant\python.exe"
if exist "%USERPROFILE%\AppData\Local\anaconda3\envs\dcquant\python.exe" set "PYTHON_CMD=%USERPROFILE%\AppData\Local\anaconda3\envs\dcquant\python.exe"

REM Fallback: try conda activate then use python
if "%PYTHON_CMD%"=="" (
    where conda >nul 2>nul
    if not errorlevel 1 (
        call conda activate dcquant >nul 2>nul
        if not errorlevel 1 (
            python --version >nul 2>nul
            if not errorlevel 1 (
                set "PYTHON_CMD=python"
            )
        )
    )
)

if "%PYTHON_CMD%"=="" (
    echo [FAIL] dcquant env not found. Run: python setup_wizard.py --auto-fix
    echo.
    pause
    exit /b 1
)

echo [OK] Python: %PYTHON_CMD%
echo.

REM ---- Set UTF-8 encoding ----
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

REM ---- Start Streamlit ----
echo [INFO] Starting QuantScout...
echo [INFO] Browser will open http://localhost:8501 in 3 seconds
echo [INFO] Real-time logs (Streamlit + strategy) will appear below
echo.

REM Open browser after 3 seconds
start "" /b powershell -NoProfile -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:8501'"

REM Run Streamlit in foreground (logs show in this window)
"%PYTHON_CMD%" -m streamlit run Home.py --server.port 8501 --server.headless true --server.address 127.0.0.1 --logger.level info --server.runOnSave false

if errorlevel 1 (
    echo.
    echo [FAIL] Start failed. Error code: %errorlevel%
    echo [INFO] Try: pip install -r requirements.txt
    echo.
)

echo.
echo ============================================================
echo  Service stopped
echo ============================================================
pause
