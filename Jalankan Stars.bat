@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if not errorlevel 1 (
    py -3 "%~dp0Stars.py" --listen
    if errorlevel 1 pause
    exit /b
)

where python >nul 2>nul
if not errorlevel 1 (
    python "%~dp0Stars.py" --listen
    if errorlevel 1 pause
    exit /b
)

echo Python tidak ditemukan. Pasang Python 3 dan aktifkan opsi Add Python to PATH.
pause
