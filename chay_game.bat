@echo off
cd /d "%~dp0"
title Co Vua AI - Game Launcher
cls
echo ========================================================
echo               KHOI DONG TRO CHOI CO VUA AI
echo ========================================================
echo Thuat toan: Minimax va Alpha-Beta Pruning
echo Dang mo giao dien game...
echo.

python main.py

if errorlevel 1 (
    echo.
    echo [LOI] Khong the khoi chay tro choi.
    echo Vui long kiem tra Python va cac thu vien: pip install -r requirements.txt
    pause
)
