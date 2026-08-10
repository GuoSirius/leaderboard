@echo off
REM A股每日市场情绪日报 - 一键生成（双击运行）
REM 用法: 直接双击；或命令行 run_daily.bat [--date 2026-08-07] [--refresh-ref] [--only-report] [--skip-bj]
SET PY=C:/Users/Admin/.workbuddy/binaries/python/envs/default/Scripts/python.exe
"%PY%" "%~dp0run_daily.py" %*
echo.
echo 按任意键关闭...
pause >nul
