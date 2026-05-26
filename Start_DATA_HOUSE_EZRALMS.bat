@echo off
REM ============================================
REM DATA_HOUSE_EZRALMS - Web UI Launcher
REM ============================================

echo.
echo ============================================
echo     DATA_HOUSE_EZRALMS
echo     PDF/Web to JSON Converter
echo ============================================
echo.

REM Change to DATA_HOUSE_EZRALMS directory
cd /d "%~dp0\DATA_HOUSE_EZRALMS"

echo [INFO] Working directory: %CD%

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [OK] Python found
python --version

echo.
echo [INFO] Starting DATA_HOUSE_EZRALMS Web UI...
echo [INFO] Please wait...
echo.

REM Start Flask server
python server.py

echo.
echo ============================================
echo     Thank you for using DATA_HOUSE_EZRALMS!
echo ============================================
timeout /t 2 /nobreak >nul
