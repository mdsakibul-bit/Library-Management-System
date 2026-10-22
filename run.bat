@echo off
title LibraryDesk - Library Management System
cd /d "%~dp0"
echo ============================================
echo   LibraryDesk - Library Management System
echo ============================================
echo.
python --version >nul 2>&1
if errorlevel 1 (
  echo Python was not found. Install Python 3 from https://www.python.org/downloads/
  echo Make sure to tick "Add Python to PATH" during installation.
  pause
  exit /b 1
)
echo Installing required package if needed...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo Flask installation failed. Check your internet connection and try again.
  pause
  exit /b 1
)
echo.
echo Starting website...
start "" http://127.0.0.1:5000
python app.py
pause
