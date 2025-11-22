@echo off
echo.
echo ===============================================
echo Starting Telegram Download Bot
echo ===============================================
echo.
echo Make sure your local Telegram Bot API server is running first!
echo.
echo Server should be started with command like:
echo telegram-bot-api.exe --api-id=27140625 --api-hash=aeb6f2a55577d1ec3c0d3b3e343844b4 --local --http-port=8081
echo.
echo Press Ctrl+C to stop the bot when needed.
echo ===============================================
echo.

cd /d "D:\Projects\Telegram_Down"

echo Starting Telegram Download Bot...
python telegram_download_bot.py

pause