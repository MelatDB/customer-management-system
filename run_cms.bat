@echo off
setlocal
title Customer Management System
cd /d "%~dp0"

echo ==========================================
echo   Customer Management System Launcher
echo ==========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python is not installed or not available in PATH.
    echo Install Python 3.11+ and make sure "Add Python to PATH" is enabled.
    echo.
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo requirements.txt was not found in this folder.
    echo.
    pause
    exit /b 1
)

echo Checking and installing required packages...
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo Failed to install the required packages.
    echo Check your internet connection and Python installation, then try again.
    echo.
    pause
    exit /b 1
)

echo.
echo Starting the application...
start "" http://127.0.0.1:5000
python app.py

echo.
echo The application has stopped.
pause
endlocal
