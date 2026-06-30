@echo off
REM ===========================================================================
REM  Double-click this on Windows to convert every video in this folder to MP3.
REM  It will install Python automatically if you don't have it. ffmpeg is
REM  handled by the script. Needs an internet connection the first time.
REM ===========================================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows-setup.ps1" %*
if errorlevel 1 (
    echo.
    echo Something went wrong. See the messages above.
    pause
)
exit /b %errorlevel%
