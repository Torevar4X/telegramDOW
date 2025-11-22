# Deployment on Pella.app

This project is configured for deployment on Pella.app.

## Prerequisites

1. A Telegram bot token from @BotFather
2. A Pella.app account

## Step-by-Step Deployment Guide

### Step 1: Prepare Your Bot Token
1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather
3. Use the `/newbot` command and follow the instructions to create your bot
4. Copy the bot token provided by BotFather

### Step 2: Deploy to Pella.app
1. Go to https://www.pella.app/
2. Sign in to your account
3. Create a new project/bot
4. Connect your GitHub repository (the one we just created: https://github.com/Torevar4X/telegramDOW.git)
5. Or directly upload the project files

### Step 3: Configure Environment Variables
1. In your Pella.app dashboard, find the environment variables section
2. Add a new environment variable:
   - Key: `BOT_TOKEN`
   - Value: Your actual bot token from Step 1

### Step 4: Verify Configuration
The project is already configured to work on Pella.app:
- `requirements.txt` specifies all needed Python dependencies
- `Procfile` defines how to run the application
- `runtime.txt` specifies the Python version
- `api_config.json` is set to use the official API by default
- The bot code is modified to use environment variables for the token

### Step 5: Start the Bot
1. Once deployed, Pella.app will automatically install dependencies and start the bot
2. Check the logs to ensure the bot started successfully
3. If you see a message like "[BOT] Bot started successfully!", the bot is running

### Step 6: Test Your Bot
1. Search for your bot on Telegram
2. Send `/start` to verify it's responding

## Important Notes

- The bot is configured to use the official Telegram API by default, which means:
  - File size limit is 50-100MB (instead of 2GB possible with local API)
  - No need to run a separate API server
  - Simpler deployment process

- Remember to secure your bot token and never commit it to version control.

## Troubleshooting

If the bot doesn't respond:
1. Check the Pella.app logs for any error messages
2. Verify your bot token is correctly set as an environment variable
3. Make sure your bot isn't blocked in any chats

For enhanced capabilities (larger file support), you would need to set up a local API server, which might not be possible on all hosting platforms like Pella.app.