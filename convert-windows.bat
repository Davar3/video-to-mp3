@echo off
setlocal
title Convert videos to MP3
cd /d "%~dp0"

echo ============================================
echo    Convert videos to MP3
echo ============================================
echo.

REM --- Find a working Python 3 (prefer the 'py' launcher; skip the Store stub) ---
set "PYCMD="

py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 set "PYCMD=py -3"

if not defined PYCMD (
    python -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PYCMD=python"
)

if not defined PYCMD (
    python3 -c "import sys" >nul 2>nul
    if not errorlevel 1 set "PYCMD=python3"
)

if not defined PYCMD goto NOPYTHON

REM --- Run the converter. ffmpeg is used from the bundled 'bin' folder if present. ---
%PYCMD% "%~dp0convert_to_mp3.py" --no-pause %*
echo.
echo Finished. You can close this window.
pause
exit /b 0

:NOPYTHON
echo Python is not installed on this computer, so the converter cannot run yet.
echo.
where winget >nul 2>nul
if not errorlevel 1 (
    echo Installing Python automatically ^(this needs an internet connection^)...
    echo A Windows prompt may ask for permission - please click Yes.
    echo.
    winget install -e --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
    echo.
    echo If Python installed successfully, please CLOSE this window
    echo and double-click this file again.
) else (
    echo Please install Python from:  https://www.python.org/downloads/
    echo IMPORTANT: during setup, tick "Add python.exe to PATH".
    echo Then run this file again.
    start "" "https://www.python.org/downloads/"
)
echo.
pause
exit /b 1
