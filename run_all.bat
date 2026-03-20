@echo off
setlocal enableextensions enabledelayedexpansion
cd /d "%~dp0"
title Inventory MVP Launcher

set "LOG_DIR=%~dp0logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\run_all.log"

echo ==================================================>>"%LOG_FILE%"
echo [START] %date% %time%>>"%LOG_FILE%"
echo [INFO] Working dir: %~dp0>>"%LOG_FILE%"
echo ==================================================>>"%LOG_FILE%"
echo [INFO] Logging to: "%LOG_FILE%"
echo [INFO] Logging to: "%LOG_FILE%">>"%LOG_FILE%"

echo [1/8] Check uv ...
echo [1/8] Check uv ...>>"%LOG_FILE%"
call :RUN "where uv"
if errorlevel 1 (
  echo [INFO] uv not found, installing via PowerShell installer...
  echo [INFO] uv not found, installing via PowerShell installer...>>"%LOG_FILE%"
  call :RUN "powershell -NoProfile -ExecutionPolicy Bypass -Command \"irm https://astral.sh/uv/install.ps1 ^| iex\""
)

REM refresh PATH for uv
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\Programs\uv;%PATH%"
call :RUN "where uv"
if errorlevel 1 goto ERR_UV

echo [2/8] Check Node.js ...
echo [2/8] Check Node.js ...>>"%LOG_FILE%"
call :RUN "where node"
if errorlevel 1 (
  echo [INFO] Node.js not found, installing Node.js LTS via PowerShell MSI...
  echo [INFO] Node.js not found, installing Node.js LTS via PowerShell MSI...>>"%LOG_FILE%"
  call :RUN "powershell -NoProfile -ExecutionPolicy Bypass -Command \"$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://nodejs.org/dist/v20.19.1/node-v20.19.1-x64.msi'; $msi=Join-Path $env:TEMP 'node-lts-x64.msi'; Invoke-WebRequest -Uri $url -OutFile $msi; Start-Process msiexec.exe -Wait -ArgumentList '/i', $msi, '/qn', '/norestart'\""
)

REM refresh PATH for node
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%LOCALAPPDATA%\Programs\nodejs;%PATH%"
call :RUN "where node"
if errorlevel 1 goto ERR_NODE

echo [3/8] Install Python by uv ...
echo [3/8] Install Python by uv ...>>"%LOG_FILE%"
call :RUN "uv python install 3.11"
if errorlevel 1 goto ERR_PY_INSTALL

echo [4/8] Create/update virtual environment ...
echo [4/8] Create/update virtual environment ...>>"%LOG_FILE%"
call :RUN "uv venv .venv --python 3.11 --clear"
if errorlevel 1 goto ERR_VENV

echo [5/8] Install backend deps by uv ...
echo [5/8] Install backend deps by uv ...>>"%LOG_FILE%"
call :RUN "uv pip install --python .venv\Scripts\python.exe -r requirements.txt"
if errorlevel 1 goto ERR_BACKEND_DEPS

echo [6/8] Install frontend deps ...
echo [6/8] Install frontend deps ...>>"%LOG_FILE%"
cd /d "%~dp0frontend"
call :RUN "npm install"
if errorlevel 1 goto ERR_FRONTEND_DEPS

echo [7/8] Build frontend ...
echo [7/8] Build frontend ...>>"%LOG_FILE%"
call :RUN "npm run build"
if errorlevel 1 goto ERR_FRONTEND_BUILD

echo [8/8] Start backend and frontend services ...
echo [8/8] Start backend and frontend services ...>>"%LOG_FILE%"
cd /d "%~dp0"
start "backend" cmd /k "cd /d ""%~dp0"" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

REM wait a moment, then open frontend in default browser
>>"%LOG_FILE%" echo [RUN] powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5173'"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5173'" >>"%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [WARN] Failed to auto-open browser. Please open http://127.0.0.1:5173 manually.
  echo [WARN] Failed to auto-open browser.>>"%LOG_FILE%"
)

echo.
echo [OK] Backend:  http://127.0.0.1:8000/docs
echo [OK] Frontend: http://127.0.0.1:5173
echo [OK] Backend:  http://127.0.0.1:8000/docs>>"%LOG_FILE%"
echo [OK] Frontend: http://127.0.0.1:5173>>"%LOG_FILE%"
echo [END] %date% %time%>>"%LOG_FILE%"
echo.
echo Press any key to close this launcher...
pause >nul
exit /b 0

:RUN
set "_cmd=%~1"
echo [RUN] !_cmd!>>"%LOG_FILE%"
cmd /c "!_cmd!" >>"%LOG_FILE%" 2>&1
set "_rc=%errorlevel%"
echo [EXIT] !_rc!>>"%LOG_FILE%"
exit /b !_rc!

:ERR_UV
echo [ERROR] Failed to install/find uv.
echo [ERROR] Failed to install/find uv.>>"%LOG_FILE%"
goto END_FAIL

:ERR_NODE
echo [ERROR] Failed to install/find Node.js.
echo [ERROR] Failed to install/find Node.js.>>"%LOG_FILE%"
goto END_FAIL

:ERR_PY_INSTALL
echo [ERROR] Failed to install Python by uv.
echo [ERROR] Failed to install Python by uv.>>"%LOG_FILE%"
goto END_FAIL

:ERR_VENV
echo [ERROR] Failed to create/update .venv.
echo [ERROR] Failed to create/update .venv.>>"%LOG_FILE%"
goto END_FAIL

:ERR_BACKEND_DEPS
echo [ERROR] Failed to install backend dependencies.
echo [ERROR] Failed to install backend dependencies.>>"%LOG_FILE%"
goto END_FAIL

:ERR_FRONTEND_DEPS
echo [ERROR] Failed to install frontend dependencies.
echo [ERROR] Failed to install frontend dependencies.>>"%LOG_FILE%"
goto END_FAIL

:ERR_FRONTEND_BUILD
echo [ERROR] Failed to build frontend.
echo [ERROR] Failed to build frontend.>>"%LOG_FILE%"
goto END_FAIL

:END_FAIL
echo.
echo [FAIL] Script failed. Please send me the full error text in this window.
echo [FAIL] Script failed. See log: "%LOG_FILE%"
echo [FAIL] Script failed. Please send me the full error text in this window.>>"%LOG_FILE%"
echo [END] %date% %time%>>"%LOG_FILE%"
pause
exit /b 1
