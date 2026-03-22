@echo off
title Transcribe Menu — Uninstall
echo.
echo  Removing context menu entries...
reg delete "HKCU\Software\Classes\SystemFileAssociations\audio\shell\Transcribe" /f >nul 2>&1
reg delete "HKCU\Software\Classes\SystemFileAssociations\video\shell\Transcribe" /f >nul 2>&1
echo  Done. Right-click entries removed.
echo.
pause
