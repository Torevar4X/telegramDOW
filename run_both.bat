@echo off
echo.
echo ===============================================
echo Running Telegram Download Bot (Local API)
echo ===============================================
echo.

cd /d "%~dp0"

set /p BOT_TOKEN="Enter your bot token: "
set /p API_ID="Enter your API ID: "
set /p API_HASH="Enter your API hash: "

echo Starting Telegram Download Bot with local API server...
python deploy.py --bot-token=%BOT_TOKEN% --api-id=%API_ID% --api-hash=%API_HASH% --use-local-api

echo.
echo Bot and API server stopped.
echo ===============================================
echo.

pause