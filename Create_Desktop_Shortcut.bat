@echo off
chcp 65001 >nul
REM ============================================
REM EZRA LMS - Create Desktop Shortcut
REM ============================================

echo.
echo ============================================
echo     EZRA LMS - Desktop Shortcut Creator
echo ============================================
echo.

REM Get the current directory (where the script is located)
set "EZRA_HOME=%~dp0"
set "EZRA_HOME=%EZRA_HOME:~0,-1%"

REM Define paths
set "BATCH_FILE=%EZRA_HOME%\Start_EZRA_WebUI.bat"
set "ICON_FILE=%EZRA_HOME%\static\images\ezra-logo.svg"
set "DESKTOP=%USERPROFILE%\Desktop"
set "SHORTCUT_NAME=EZRA LMS WebUI.lnk"
set "SHORTCUT_PATH=%DESKTOP%\%SHORTCUT_NAME%"

REM Verify batch file exists
if not exist "%BATCH_FILE%" (
    echo [ERROR] Start_EZRA_WebUI.bat not found!
    echo [ERROR] Please make sure this script is in the EZRALMS_data_base folder.
    pause
    exit /b 1
)

echo [INFO] Creating desktop shortcut...
echo [INFO] EZRA Home: %EZRA_HOME%
echo [INFO] Desktop: %DESKTOP%
echo.

REM Create VBScript to create shortcut
set "VBS_FILE=%TEMP%\CreateShortcut.vbs"
(
echo Set oWS = WScript.CreateObject("WScript.Shell"^)
echo sLinkFile = "%SHORTCUT_PATH%"
echo Set oLink = oWS.CreateShortcut(sLinkFile^)
echo oLink.TargetPath = "%BATCH_FILE%"
echo oLink.WorkingDirectory = "%EZRA_HOME%"
echo oLink.Description = "EZRA LMS - Attendance Management Web UI"
echo oLink.IconLocation = "%SYSTEMROOT%\System32\SHELL32.dll, 14"
) > "%VBS_FILE%"

REM Run VBScript to create shortcut
wscript //nologo "%VBS_FILE%"

REM Clean up VBScript
del "%VBS_FILE%"

REM Verify shortcut was created
if exist "%SHORTCUT_PATH%" (
    echo.
    echo ============================================
    echo     [SUCCESS] Shortcut Created!
    echo ============================================
    echo.
    echo Shortcut Name: %SHORTCUT_NAME%
    echo Location: %DESKTOP%
    echo.
    echo You can now launch EZRA LMS WebUI by double-clicking
    echo the shortcut on your Desktop!
    echo.
    echo ============================================
) else (
    echo.
    echo [ERROR] Failed to create shortcut!
    echo.
    echo Please try creating the shortcut manually:
    echo 1. Right-click on Desktop
    echo 2. New -> Shortcut
    echo 3. Browse to: %BATCH_FILE%
    echo 4. Name it: EZRA LMS WebUI
    echo.
)

echo.
pause
