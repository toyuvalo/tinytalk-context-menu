@echo off
setlocal
title TinyTalk — Build
cd /d "%~dp0"

echo.
echo  ================================
echo   TinyTalk Build
echo  ================================
echo.

python -c "import PyInstaller" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing PyInstaller...
    pip install pyinstaller --quiet
)

echo Generating icon...
python make_icon.py

echo Building TinyTalk_Setup.exe...
pyinstaller --onefile --windowed ^
    --name "TinyTalk_Setup" ^
    --icon "icon.ico" ^
    --add-data "tinytalk.py;." ^
    --add-data "icon.ico;." ^
    installer.py

if not exist dist\TinyTalk_Setup.exe (
    echo Build failed.
    pause & exit /b 1
)

REM Code-sign (Azure Artifact Signing, publisher "Yuval Olsha"). Set NOSIGN=1 to skip.
if not defined AZSIGN set "AZSIGN=G:\dev-tools\artifact-signing-client\azsign.cmd"
if not defined NOSIGN (
    call "%AZSIGN%" dist\TinyTalk_Setup.exe
    if errorlevel 1 (
        echo Signing failed. Check az login, or set NOSIGN=1.
        pause & exit /b 1
    )
)

echo.
echo  ================================
echo   Done: dist\TinyTalk_Setup.exe
echo  ================================
echo.
pause
endlocal
