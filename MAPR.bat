@echo off
REM MAPR Command Runner
REM Usage: MAPR [command] [options]

cd /d "%~dp0"

if "%1"=="done" (
    python mapr_updater.py add-done --item "%2" --notes "%3"
    goto :eof
)

if "%1"=="pending" (
    python mapr_updater.py add-pending --item "%2" --notes "%3"
    goto :eof
)

if "%1"=="note" (
    python mapr_updater.py add-note --title "%2" --content "%3"
    goto :eof
)

if "%1"=="status" (
    python mapr_updater.py status
    goto :eof
)

echo.
echo MAPR Command Runner
echo =====================
echo.
echo Usage:
echo   MAPR done    "Item yang selesai"   "Catatan opsional"
echo   MAPR pending "Item yang belum"     "Target opsional"
echo   MAPR note    "Judul"               "Konten catatan"
echo   MAPR status
echo.
echo Contoh:
echo   MAPR done "Implementasi RAG database" "Sudah ditesting"
echo   MAPR pending "SVG Generation" "Butuh AI integration"
echo   MAPR note "Session 2026-05-10" "Progress mingguan..."
echo.
pause