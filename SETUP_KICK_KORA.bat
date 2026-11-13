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
%PYEXE% setup_key.py
if errorlevel 1 pause
endlocal
