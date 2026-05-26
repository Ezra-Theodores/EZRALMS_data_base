# Create Desktop Shortcut for EZRA LMS WebUI
# ===========================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Creating Desktop Shortcut" -ForegroundColor Cyan
Write-Host "  EZRA LMS WebUI" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Define paths
$EZRA_HOME = $PSScriptRoot
$BATCH_FILE = Join-Path $EZRA_HOME "Start_EZRA_WebUI.bat"
$DESKTOP = [Environment]::GetFolderPath("Desktop")
$SHORTCUT_NAME = "EZRA LMS WebUI.lnk"
$SHORTCUT_PATH = Join-Path $DESKTOP $SHORTCUT_NAME

# Verify batch file exists
if (-not (Test-Path $BATCH_FILE)) {
    Write-Host "[ERROR] Start_EZRA_WebUI.bat not found!" -ForegroundColor Red
    Write-Host "[ERROR] Please make sure this script is in the EZRALMS_data_base folder." -ForegroundColor Red
    Pause
    exit 1
}

Write-Host "[INFO] Creating shortcut..." -ForegroundColor Yellow
Write-Host "[INFO] EZRA Home: $EZRA_HOME" -ForegroundColor Gray
Write-Host "[INFO] Desktop: $DESKTOP" -ForegroundColor Gray
Write-Host ""

# Create shortcut using WScript.Shell
try {
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut($SHORTCUT_PATH)
    $Shortcut.TargetPath = $BATCH_FILE
    $Shortcut.WorkingDirectory = $EZRA_HOME
    $Shortcut.Description = "EZRA LMS - Attendance Management Web UI"
    $Shortcut.IconLocation = "$env:SystemRoot\System32\SHELL32.dll, 14"
    $Shortcut.Save()

    Write-Host "========================================" -ForegroundColor Green
    Write-Host "     [SUCCESS] Shortcut Created!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Shortcut Name: $SHORTCUT_NAME" -ForegroundColor Cyan
    Write-Host "Location: $DESKTOP" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "You can now launch EZRA LMS WebUI by" -ForegroundColor White
    Write-Host "double-clicking the shortcut on your Desktop!" -ForegroundColor White
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to create shortcut!" -ForegroundColor Red
    Write-Host "[ERROR] $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please try creating the shortcut manually:" -ForegroundColor Yellow
    Write-Host "1. Right-click on Desktop" -ForegroundColor Gray
    Write-Host "2. New -> Shortcut" -ForegroundColor Gray
    Write-Host "3. Browse to: $BATCH_FILE" -ForegroundColor Gray
    Write-Host "4. Name it: EZRA LMS WebUI" -ForegroundColor Gray
}

Write-Host ""
Pause
