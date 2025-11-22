@echo off
echo.
echo ===============================================
echo Starting Local Telegram Bot API Server
echo ===============================================
echo.
echo NOTE: You need to obtain your own api_id and api_hash from https://my.telegram.org
echo.
echo Replace YOUR_API_ID and YOUR_API_HASH in this file with your actual values.
echo.
echo Press Ctrl+C to stop the server when needed.
echo ===============================================
echo.

REM Replace these values with your actual api_id and api_hash from https://my.telegram.org
set API_ID=27140625
set API_HASH=aeb6f2a55577d1ec3c0d3b3e343844b4

cd /d "D:\Projects\Telegram_Down\telegram-bot-api\bin"

if "%API_ID%" == "YOUR_API_ID" (
    echo ERROR: Please edit this file and replace YOUR_API_ID and YOUR_API_HASH with your actual values!
    pause
    exit /b 1
)

echo Starting Telegram Bot API Server on port 8081...
telegram-bot-api.exe --api-id=%API_ID% --api-hash=%API_HASH% --local --http-port=8081

pause