# Telegram File Download Bot - Project Context

## Project Overview

The Telegram File Download Bot is a Python-based bot that allows users to download files from direct links and send them to Telegram. The project is designed to handle large files (up to 4GB with local API), which exceeds the standard Telegram bot file size limit of 50MB-100MB.

## Architecture & Components

The project consists of two main components:

1. **Python Bot Script** (`telegram_download_bot.py`): The main Telegram bot application that handles user interactions, file downloading, and upload to Telegram
2. **Local Telegram Bot API Server**: A local instance of the Telegram Bot API server that allows for larger file uploads (up to 2GB vs 50MB on the official API)

## Key Features

- Download files from direct links and send to Telegram
- Support for large files (up to 2GB with local API)
- Interactive UI with inline keyboards
- Progress tracking for downloads and uploads
- File renaming capability
- Retry logic for failed uploads
- Automatic cleanup of downloaded files

## Dependencies

The bot requires the following Python packages:
- `python-telegram-bot` - Main Telegram bot framework
- `aiohttp` - Asynchronous HTTP client for file downloads
- `aiofiles` - Asynchronous file operations
- `validators` - URL validation

## Configuration

The bot uses `api_config.json` for API server configuration:
- `use_local_api`: Whether to use the local API server (default: true)
- `local_api_url`: URL of the local API server (default: http://localhost:8081)
- `official_api_url`: URL of official API server (fallback)

## Main Files

- `telegram_download_bot.py` - Main bot application with download/upload logic
- `api_config.json` - API server configuration
- `start_bot.bat` - Batch script to start the bot
- `start_local_api_server.bat` - Batch script to start the local API server
- `INSTALLATION_GUIDE.md` - Complete setup instructions

## Usage

1. The local API server must be running before starting the bot
2. The bot token must be set in `telegram_download_bot.py`
3. Run the bot with `python telegram_download_bot.py`
4. Use `/download` command to start downloading files from direct links

## Development Notes

- The bot includes comprehensive error handling and progress tracking
- File size limits are enforced (2GB maximum due to Telegram limitations)
- The system automatically cleans up downloaded files after upload
- Connection timeouts are configured to handle large file downloads
- Includes retry logic for failed uploads with exponential backoff

## Running the Project

1. Ensure the local Telegram Bot API server is running on port 8081
2. Install Python dependencies: `pip install python-telegram-bot aiohttp aiofiles validators`
3. Run the bot: `python telegram_download_bot.py` or `start_bot.bat`

## Security Considerations

- Bot tokens and API credentials are hardcoded or should be environment variables
- The local API server requires valid `api_id` and `api_hash` from https://my.telegram.org
- No authentication mechanism for the bot beyond Telegram's standard bot authentication