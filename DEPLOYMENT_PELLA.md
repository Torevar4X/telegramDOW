# Deployment on Pella.app

This project is configured for deployment on Pella.app.

## Prerequisites

1. A Telegram bot token from @BotFather
2. A Pella.app account
3. (Optional) Telegram API credentials (api_id and api_hash) from https://my.telegram.org for larger file support

## Step-by-Step Deployment Guide

### Step 1: Prepare Your Bot Token
1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather
3. Use the `/newbot` command and follow the instructions to create your bot
4. Copy the bot token provided by BotFather

### Step 2: (Optional) Get API Credentials for Larger File Support
If you want to support files larger than 50-100MB (up to 2GB):
1. Go to https://my.telegram.org
2. Sign in with your Telegram account
3. Click on "API development tools"
4. Create a new application
5. Note your API_ID and API_HASH values

### Step 3: Deploy to Pella.app
1. Go to https://www.pella.app/
2. Sign in to your account
3. Create a new project/bot
4. Connect your GitHub repository (the one we just created: https://github.com/Torevar4X/telegramDOW.git)
5. Or directly upload the project files

### Step 4: Configure Environment Variables
1. In your Pella.app dashboard, find the environment variables section
2. Add the following environment variables:
   - `BOT_TOKEN`: Your actual bot token from Step 1
   - (Optional) `API_ID` and `API_HASH`: Your API credentials from Step 2 for larger file support

### Step 5: Select the Python File to Run
1. In your Pella.app configuration, make sure to run `run_pella.py` as your main Python file
2. This script handles both the local API server (if credentials provided) and the bot in a single file as required by Pella

### Step 6: Verify Configuration
The project is already configured to work on Pella.app:
- `requirements.txt` specifies all needed Python dependencies
- `Procfile` defines how to run the application
- `runtime.txt` specifies the Python version
- `api_config.json` is set to use the official API by default
- The `run_pella.py` script handles starting both the local API server and the bot in a single Python file
- The bot code is modified to use environment variables for the token

### Step 7: Start the Bot
1. Once deployed, Pella.app will automatically install dependencies and start the bot
2. If you provided API credentials, the script will also start a local API server for larger file support
3. Check the logs to ensure the bot started successfully
4. If you see a message like "[BOT] Bot started successfully!", the bot is running

### Step 8: Test Your Bot
1. Search for your bot on Telegram
2. Send `/start` to verify it's responding

## Important Notes

- The bot can use either the official Telegram API or a local API server:
  - With only `BOT_TOKEN`: Uses official API with 50-100MB file size limit
  - With `BOT_TOKEN`, `API_ID`, and `API_HASH`: Tries to use local API with up to 2GB file size limit
  - The `run_pella.py` script automatically handles which configuration to use based on available environment variables

- When using local API on Pella:
  - The script attempts to download and run the Telegram Bot API server automatically
  - Some hosting platforms may have restrictions that prevent running additional processes
  - If the local API server fails to start, the bot will automatically fall back to the official API
  - Monitor your deployment logs to see which mode is active

- Remember to secure your bot token and API credentials and never commit them to version control.

## Troubleshooting

If the bot doesn't respond:
1. Check the Pella.app logs for any error messages
2. Verify your bot token is correctly set as an environment variable
3. Make sure your bot isn't blocked in any chats
4. If using local API, check that API_ID and API_HASH are correctly set

For enhanced capabilities (larger file support), make sure you've set the API_ID and API_HASH environment variables.