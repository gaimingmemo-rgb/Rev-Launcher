@echo off
title Rev-Launcher // Tactical Ground-Up Edition
echo ========================================================
echo        REV-LAUNCHER // TACTICAL GROUND-UP CORE
echo           Hydra Sources & Revision Suite Hub
echo ========================================================
echo Initializing Native PySide6 Engine and Rev-Network P2P...
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Rev-Launcher exited with code %ERRORLEVEL%
    pause
)
