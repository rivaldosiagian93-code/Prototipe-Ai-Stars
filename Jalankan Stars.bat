@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=%~dp0.venv\Scripts\python.exe"
if exist "%PYTHON%" goto :python_ready

where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv "%~dp0.venv"
    if errorlevel 1 goto :setup_failed
    goto :python_ready
)

where python >nul 2>nul
if not errorlevel 1 (
    python -m venv "%~dp0.venv"
    if errorlevel 1 goto :setup_failed
    goto :python_ready
)

echo Python tidak ditemukan. Pasang Python 3 lalu coba jalankan shortcut ini lagi.
pause
exit /b 1

:python_ready
"%PYTHON%" -c "import speech_recognition, sounddevice" >nul 2>nul
if errorlevel 1 (
    echo Menyiapkan dukungan mikrofon Stars...
    "%PYTHON%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 goto :setup_failed
)

"%PYTHON%" "%~dp0Stars.py" --listen
if errorlevel 1 pause
exit /b

:setup_failed
echo Stars gagal disiapkan. Periksa koneksi internet dan coba jalankan shortcut lagi.
pause
exit /b 1
