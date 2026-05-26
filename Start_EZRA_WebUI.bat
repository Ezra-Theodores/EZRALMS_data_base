@echo off
REM ============================================
REM EZRA LMS - Web UI Launcher
REM ============================================

echo.
echo ============================================
echo     EZRA LMS - Attendance Management
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"

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
echo [INFO] Starting EZRA LMS Web UI...
echo [INFO] Please wait...
echo.

REM Start Flask app in background
start /b python app.py > webui.log 2>&1

REM Wait for server to start
echo [INFO] Waiting for server to start...
timeout /t 3 /nobreak >nul

REM Check if server is running
ping -n 1 127.0.0.1 -p 5002 >nul 2>&1
if not errorlevel 1 (
    echo [OK] Server is running!
    echo.
    echo ============================================
    echo     Opening browser...
    echo ============================================
    start http://localhost:5002
) else (
    echo [WARNING] Server may still be starting...
    echo [INFO] Opening browser anyway...
    start http://localhost:5002
)

echo.
echo ============================================
echo     Web UI should open in your browser
echo     URL: http://localhost:5002
echo ============================================
echo.
echo [INFO] Press any key to stop the server...
pause >nul

echo.
echo [INFO] Stopping server...
REM Kill python process running app.py
for /f "tokens=2" %%a in ('tasklist ^| findstr python') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo [OK] Server stopped
echo.
echo ============================================
echo     Thank you for using EZRA LMS!
echo ============================================
timeout /t 2 /nobreak >nul
