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

echo Building TinyTalk_Setup.exe...
pyinstaller --onefile --windowed ^
    --name "TinyTalk_Setup" ^
    --add-data "tinytalk.py;." ^
    installer.py

if not exist dist\TinyTalk_Setup.exe (
    echo Build failed.
    pause & exit /b 1
)

echo.
echo  ================================
echo   Done: dist\TinyTalk_Setup.exe
echo  ================================
echo.
pause
endlocal
