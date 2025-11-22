@echo off
echo.
echo ===============================================
echo Setting up Telegram Download Bot Environment
echo ===============================================
echo.

cd /d "%~dp0"

echo Installing Python dependencies...
python -m pip install -r requirements.txt

echo.
echo Downloading Telegram Bot API Server (if needed)...
echo Please provide your API credentials when prompted
echo Get them from https://my.telegram.org

set /p API_ID="Enter your API ID: "
set /p API_HASH="Enter your API hash: "

echo.
echo Setting up configuration...
python deploy.py --api-id=%API_ID% --api-hash=%API_HASH% --setup-only

echo.
echo Setup complete! You can now run the bot with run_bot.bat or run_both.bat
echo ===============================================
echo.

pause