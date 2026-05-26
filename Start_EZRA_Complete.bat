@echo off
chcp 65001 >nul
REM ============================================
REM EZRA LMS - Complete Web UI Launcher
REM Users & Curriculum Management
REM ============================================

echo.
echo ============================================
echo     EZRA LMS - Complete Web UI
echo     Users & Curriculum Management
echo ============================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo [ERROR] Please install Python 3.8 or higher
    pause
    exit /b 1
)

echo [OK] Python found:
python --version
echo.

REM Check if required packages are installed
echo [INFO] Checking dependencies...
python -c "import flask" 2>nul
if errorlevel 1 (
    echo [INFO] Installing required packages...
    pip install flask python-dotenv -q
    echo [OK] Dependencies installed
) else (
    echo [OK] Dependencies satisfied
)
echo.

echo [INFO] Starting EZRA LMS Complete Web UI...
echo [INFO] Initializing database...
echo.

REM Start Flask app in background
start /b python app_complete.py > webui_complete.log 2>&1

REM Wait for server to start
echo [INFO] Waiting for server to start...
timeout /t 4 /nobreak >nul

REM Check if server is running
netstat -an | findstr ":5000" >nul
if not errorlevel 1 (
    echo [OK] Server is running on port 5000!
    echo.
    echo ============================================
    echo     Opening browser...
    echo ============================================
    echo.
    start http://localhost:5000
) else (
    echo [WARNING] Server may still be starting...
    echo [INFO] Opening browser anyway...
    start http://localhost:5000
)

echo.
echo ============================================
echo     Web UI should open in your browser
echo     URL: http://localhost:5000
echo ============================================
echo.
echo [INFO] Features:
echo   - Users Management (Students, Teachers, Admins)
echo   - Curriculum: Grades 1-12
echo   - Classes, Topics, Sub-topics
echo   - Materials and Quizzes
echo   - Tree View Navigation
echo   - Data House Integration
echo.
echo [INFO] Press any key to stop the server...
pause >nul

echo.
echo [INFO] Stopping server...
REM Kill python process running app_complete.py
for /f "tokens=2" %%a in ('tasklist ^| findstr python') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo [OK] Server stopped
echo.
echo ============================================
echo     Thank you for using EZRA LMS!
echo ============================================
timeout /t 2 /nobreak >nul
