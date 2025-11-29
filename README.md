# Telegram File Download Bot

A robust bot for downloading and transferring large files from direct links to Telegram.

## Features

- Download files from direct links and send to Telegram
- Support for large files (up to 2GB with local API)
- Interactive UI with inline keyboards
- Progress tracking for downloads and uploads
- File renaming capability
- Retry logic for failed uploads
- Automatic cleanup of downloaded files

## Deployment on Pella.app

To deploy this bot on Pella.app, follow these steps:

### 1. Environment Setup

Set the following environment variables on Pella.app:
- `BOT_TOKEN`: Your Telegram bot token from @BotFather
- (Optional) `API_ID` and `API_HASH`: Your API credentials from https://my.telegram.org for larger file support (up to 2GB files)

### 2. Configuration

The bot can be configured in two ways:
- With only `BOT_TOKEN`: Uses official API with 50-100MB file size limit
- With `BOT_TOKEN`, `API_ID`, and `API_HASH`: Uses local API with up to 2GB file size limit

### 3. Running the Bot

Use the `run_pella.py` file as the main entry point when deploying on Pella.app. This single Python file handles both the local API server (if credentials provided) and the bot as required by Pella.

### 4. Requirements

The bot requires the following dependencies:
- python-telegram-bot
- aiohttp
- aiofiles
- validators

These are specified in the `requirements.txt` file.

## Local Installation (for reference)

If you want to run this bot locally with enhanced capabilities:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. For enhanced capabilities (larger file support), you can set up a local API server:
   - Follow the instructions in INSTALLATION_GUIDE.md

3. Set your bot token as an environment variable:
   ```bash
   export BOT_TOKEN="your_bot_token_here"
   ```

4. Run the bot using the Pella deployment script (which works locally too):
   ```bash
   python run_pella.py
   ```

Or run directly:
   ```bash
   python telegram_download_bot.py
   ```

## Usage

Once the bot is running:

1. Search for your bot on Telegram
2. Use `/start` to see the welcome message
3. Use `/download` to start the download process
4. Send a direct download link to the bot
5. The bot will download the file and send it back to you