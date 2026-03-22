@echo off
setlocal enabledelayedexpansion
title Transcribe Menu — Installer
cd /d "%~dp0"

echo.
echo  ================================
echo   Transcribe Menu Installer
echo  ================================
echo.

:: ── 1. Python ─────────────────────────────────────────────────────────────────
echo [1/3] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    py --version >nul 2>&1
    if !errorlevel! neq 0 (
        echo  Python not found. Installing via winget...
        winget install --id Python.Python.3.12 -e --silent
        if !errorlevel! neq 0 (
            echo  Please install Python from https://www.python.org/downloads/
            pause & exit /b 1
        )
    )
)
echo  Python OK

:: ── 2. faster-whisper ─────────────────────────────────────────────────────────
echo [2/3] Installing faster-whisper...
python -c "import faster_whisper" >nul 2>&1
if %errorlevel% neq 0 (
    pip install faster-whisper --quiet
    if !errorlevel! neq 0 (
        echo  Failed to install faster-whisper.
        pause & exit /b 1
    )
)
echo  faster-whisper OK

:: ── 3. Registry — context menu for audio + video files ───────────────────────
echo [3/3] Registering context menu...

:: Get absolute path to this folder and the launcher
set "SCRIPT=%~dp0transcribe.py"
set "LAUNCH=%~dp0launch.vbs"

:: Find pythonw
for /f "delims=" %%i in ('where pythonw 2^>nul') do set "PYTHONW=%%i"
if not defined PYTHONW (
    for /f "delims=" %%i in ('where python 2^>nul') do set "PYTHONW=%%i"
)

:: Write the VBScript launcher (silent, no console)
(
echo Set sh = CreateObject^("WScript.Shell"^)
echo sh.Run """""!PYTHONW!"""" """"!SCRIPT!"""" """" ^& WScript.Arguments^(0^) ^& """"", 0, False
) > "!LAUNCH!"

set "CMD=wscript.exe \"!LAUNCH!\" \"%%1\""

:: Register for audio perceived type
reg add "HKCU\Software\Classes\SystemFileAssociations\audio\shell\Transcribe"          /ve /d "Transcribe to TXT" /f >nul
reg add "HKCU\Software\Classes\SystemFileAssociations\audio\shell\Transcribe\command"  /ve /d "!CMD!" /f >nul

:: Register for video perceived type
reg add "HKCU\Software\Classes\SystemFileAssociations\video\shell\Transcribe"          /ve /d "Transcribe to TXT" /f >nul
reg add "HKCU\Software\Classes\SystemFileAssociations\video\shell\Transcribe\command"  /ve /d "!CMD!" /f >nul

echo  Context menu registered

:: ── Done ──────────────────────────────────────────────────────────────────────
echo.
echo  ================================
echo   Done!
echo   Right-click any audio or video
echo   file and choose "Transcribe to TXT"
echo  ================================
echo.
echo  Note: The first transcription will download the Whisper
echo  base model (~150 MB). Subsequent runs are instant.
echo.
pause
endlocal
