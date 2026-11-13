@echo off
setlocal
cd /d "%~dp0"
chcp 437 >nul
set "PYEXE="
where py.exe >nul 2>nul
if not errorlevel 1 set "PYEXE=py"
if not defined PYEXE (
  where python.exe >nul 2>nul
  if not errorlevel 1 set "PYEXE=python"
)
if not defined PYEXE (
  echo Python was not found. Install it from https://www.python.org/downloads/windows/
  pause
  exit /b 1
)
if not exist .env (
  echo API key setup is required.
  %PYEXE% setup_key.py
  if errorlevel 1 (
    pause
    exit /b 1
  )
)
echo Starting Kick Kora at http://localhost:3000
set "CHROME="
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not defined CHROME if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set "CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe"
if defined CHROME (
  start "" "%CHROME%" "http://localhost:3000"
) else (
  echo Chrome not found in standard installation folders.
  start "" "http://localhost:3000"
)
%PYEXE% server.py
pause
endlocal
