@echo off
setlocal
cd /d "%~dp0"
title Inventory MVP Launcher

echo [1/8] Check uv ...
where uv >nul 2>nul
if errorlevel 1 (
  echo [INFO] uv not found, installing via PowerShell installer...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
)

REM refresh PATH for uv
set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%LOCALAPPDATA%\Programs\uv;%PATH%"
where uv >nul 2>nul
if errorlevel 1 goto ERR_UV

echo [2/8] Check Node.js ...
where node >nul 2>nul
if errorlevel 1 (
  echo [INFO] Node.js not found, installing Node.js LTS via PowerShell MSI...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; $ProgressPreference='SilentlyContinue'; $url='https://nodejs.org/dist/v20.19.1/node-v20.19.1-x64.msi'; $msi=Join-Path $env:TEMP 'node-lts-x64.msi'; Invoke-WebRequest -Uri $url -OutFile $msi; Start-Process msiexec.exe -Wait -ArgumentList '/i', $msi, '/qn', '/norestart'"
)

REM refresh PATH for node
set "PATH=%ProgramFiles%\nodejs;%ProgramFiles(x86)%\nodejs;%LOCALAPPDATA%\Programs\nodejs;%PATH%"
where node >nul 2>nul
if errorlevel 1 goto ERR_NODE

echo [3/8] Install Python by uv ...
uv python install 3.11
if errorlevel 1 goto ERR_PY_INSTALL

echo [4/8] Create/update virtual environment ...
uv venv .venv --python 3.11
if errorlevel 1 goto ERR_VENV

echo [5/8] Install backend deps by uv ...
uv pip install --python .venv\Scripts\python.exe -r requirements.txt
if errorlevel 1 goto ERR_BACKEND_DEPS

echo [6/8] Install frontend deps ...
cd /d "%~dp0frontend"
call npm install
if errorlevel 1 goto ERR_FRONTEND_DEPS

echo [7/8] Build frontend ...
call npm run build
if errorlevel 1 goto ERR_FRONTEND_BUILD

echo [8/8] Start backend and frontend services ...
cd /d "%~dp0"
start "backend" cmd /k "cd /d ""%~dp0"" && .venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "frontend" cmd /k "cd /d ""%~dp0frontend"" && npm run dev"

REM wait a moment, then open frontend in default browser
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:5173'"

echo.
echo [OK] Backend:  http://127.0.0.1:8000/docs
echo [OK] Frontend: http://127.0.0.1:5173
echo.
echo Press any key to close this launcher...
pause >nul
exit /b 0

:ERR_UV
echo [ERROR] Failed to install/find uv.
goto END_FAIL

:ERR_NODE
echo [ERROR] Failed to install/find Node.js.
goto END_FAIL

:ERR_PY_INSTALL
echo [ERROR] Failed to install Python by uv.
goto END_FAIL

:ERR_VENV
echo [ERROR] Failed to create/update .venv.
goto END_FAIL

:ERR_BACKEND_DEPS
echo [ERROR] Failed to install backend dependencies.
goto END_FAIL

:ERR_FRONTEND_DEPS
echo [ERROR] Failed to install frontend dependencies.
goto END_FAIL

:ERR_FRONTEND_BUILD
echo [ERROR] Failed to build frontend.
goto END_FAIL

:END_FAIL
echo.
echo [FAIL] Script failed. Please send me the full error text in this window.
pause
exit /b 1
