@echo off
echo.
echo ===============================================
echo Running Telegram Download Bot (Official API)
echo ===============================================
echo.

cd /d "%~dp0"

echo Starting Telegram Download Bot with official API...
set USE_LOCAL_API=false
python deploy.py --run-bot

echo.
echo Bot stopped.
echo ===============================================
echo.

pause