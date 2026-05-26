@echo off
REM EZRA LMS - Firestore to MySQL Sync Runner
REM ===========================================

echo ===========================================
echo EZRA LMS - Firestore to MySQL Sync
echo ===========================================
echo.

REM Change to script directory
cd /d "%~dp0"

REM Check if Python is available
python --version > nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Check if virtual environment exists, if not use system Python
if exist "venv\Scripts\python.exe" (
    set PYTHON=venv\Scripts\python.exe
    echo Using virtual environment
) else (
    set PYTHON=python
    echo Using system Python
)

REM Check if requirements are installed
echo Checking dependencies...
%PYTHON% -c "import firebase_admin" > nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo.
echo ===========================================
echo Starting Sync Process
echo ===========================================
echo.

REM Parse arguments
if "%~1"=="" (
    set SYNC_ARGS=
) else (
    set SYNC_ARGS=%*
)

REM Run the sync script
%PYTHON% sync_attendance.py %SYNC_ARGS%

set SYNC_RESULT=%ERRORLEVEL%

echo.
echo ===========================================
if %SYNC_RESULT% == 0 (
    echo Sync completed successfully!
) else (
    echo Sync failed with error code: %SYNC_RESULT%
)
echo ===========================================

REM Keep window open if double-clicked
if "%1"=="" pause

exit /b %SYNC_RESULT%
