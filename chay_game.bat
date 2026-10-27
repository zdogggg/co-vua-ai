@echo off
chcp 65001 >nul
title Cờ Vua AI - Game Launcher
cls
echo ========================================================
echo               KHỞI ĐỘNG TRÒ CHƠI CỜ VUA AI
echo ========================================================
echo Thuật toán: Minimax và Alpha-Beta Pruning
echo Đang nạp tài nguyên và mở giao diện...
echo.

python main.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [LỖI] Không thể khởi chạy trò chơi. Vui lòng kiểm tra Python và các thư viện trong requirements.txt.
    pause
)
