# Telegram File Download Bot with Local API Server

This guide provides comprehensive instructions for setting up and running the Telegram File Download Bot with a local API server for enhanced file handling capabilities.

## Overview

The Telegram File Download Bot allows users to download files from direct links and send them to Telegram. By running a local Telegram Bot API server, you'll get:
- Support for larger file uploads (up to 2GB vs 50MB on official API)
- Better performance for file operations
- Reduced dependency on official Telegram API servers
- Enhanced privacy and control

## Prerequisites

- Windows, Linux, or macOS operating system
- Python 3.8 or higher
- Git
- Telegram account to create a bot
- Telegram account to get API credentials

## Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org using your phone number
2. Log in with your Telegram account
3. Click on "API development tools"
4. Fill in the required fields to create a new application
5. Note down your:
   - **api_id** (numeric ID)
   - **api_hash** (hexadecimal hash)

## Step 2: Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Start a chat with BotFather
3. Use the `/newbot` command
4. Follow the instructions to create your bot
5. Copy the bot token provided by BotFather

## Step 3: Install the Local Telegram Bot API Server

### For Pre-built Binaries (Recommended):

1. Download the pre-built binaries for your platform:
   - Windows: Download from https://github.com/tdlib/telegram-bot-api/releases
   - Linux: `wget https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-linux` 
   - macOS: `wget https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-macos`

2. Extract the archive and place the executable in your project directory

### For Building from Source:

```bash
# Clone the repository
git clone --recursive https://github.com/tdlib/telegram-bot-api.git
cd telegram-bot-api

# Install dependencies (Ubuntu/Debian example)
sudo apt-get update
sudo apt-get install -y build-essential cmake zlib1g-dev libssl-dev gperf

# Build the server
mkdir build && cd build
cmake -DCMAKE_BUILD_TYPE=Release ..
cmake --build . --target install

# The executable will be in bin/ directory
```

## Step 4: Install Python Dependencies

```bash
pip install python-telegram-bot aiohttp aiofiles validators
```

## Step 5: Configure the Bot

1. Create a new directory for your project
2. Create the bot file `telegram_download_bot.py` with your code
3. Add your bot token to the `BOT_TOKEN` variable in the script
4. Create `api_config.json` file:

```json
{
  "use_local_api": true,
  "local_api_url": "http://localhost:8081",
  "official_api_url": "https://api.telegram.org"
}
```

## Step 6: Run the Local API Server

1. Open a command prompt/terminal
2. Navigate to the directory containing the `telegram-bot-api` executable
3. Run the server with your credentials:

```bash
# Windows
telegram-bot-api.exe --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local --http-port=8081

# Linux/macOS
./telegram-bot-api --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local --http-port=8081
```

Replace `YOUR_API_ID` and `YOUR_API_HASH` with your actual credentials from Step 1.

## Step 7: Register Your Bot with the Local Server

1. In a new command prompt/terminal, verify your bot is working with the local server:

```bash
curl -X POST http://localhost:8081/botYOUR_BOT_TOKEN/getMe
```

This should return information about your bot, confirming it's registered with the local server.

## Step 8: Run the Telegram Bot

In a new command prompt/terminal (with the local server still running):

```bash
python telegram_download_bot.py
```

The bot should now be running and connected to your local API server.

## Step 9: Using the Bot

1. Search for your bot on Telegram (using the username you created)
2. Start a chat with your bot
3. Use `/start` to see the welcome message
4. Use `/download` to start the download process
5. Send a direct download link to the bot
6. The bot will download the file and send it back to you

## Cloud Server Deployment

### For Cloud Server (Ubuntu Example):

1. Connect to your cloud server via SSH
2. Install required packages:

```bash
sudo apt update
sudo apt install python3 python3-pip git curl wget
```

3. Follow the installation steps above
4. To run the server in the background, use `screen` or `tmux`:

```bash
# Install screen
sudo apt install screen

# Start the API server in a screen session
screen -S bot_api_server
./telegram-bot-api --api-id=YOUR_API_ID --api-hash=YOUR_API_HASH --local --http-port=8081

# Detach from screen: Ctrl+A, then D
# Reattach to screen: screen -r bot_api_server
```

5. Similarly, run your bot in a separate screen session:

```bash
screen -S telegram_bot
python3 telegram_download_bot.py
```

## Security Considerations

1. **Never commit bot tokens or API credentials to version control**
2. **Use a dedicated Telegram account for API credentials**
3. **Keep your server updated and secure**
4. **Consider using a firewall to restrict access to the API server**

## Troubleshooting

### Common Issues:

**Issue**: `InvalidToken: Not Found`
- **Solution**: Make sure you registered your bot with the local server using the curl command

**Issue**: `Invalid port` error
- **Solution**: Check that your base URL is properly formatted with trailing slash

**Issue**: Server won't start
- **Solution**: Verify your api_id and api_hash are correct

**Issue**: Bot doesn't respond
- **Solution**: Check that both the API server and bot scripts are running

### Server Status Check:

```bash
# Check if API server is running
curl http://localhost:8081

# Check if your bot is registered
curl -X POST http://localhost:8081/botYOUR_BOT_TOKEN/getMe
```

## Updating and Maintenance

1. **Update the bot script**: Pull latest changes from your repository
2. **Update the API server**: Download the latest release from TDLib
3. **Update dependencies**: Run `pip install --upgrade python-telegram-bot aiohttp aiofiles validators`

## Moving Bots Between Servers

If you need to move a bot from one server to another:

1. Call the `logOut` method on the current server:
   ```bash
   curl -X POST http://CURRENT_SERVER/botTOKEN/logOut
   ```

2. The bot will be deregistered and ready to be used with the new server

## File Limits and Capabilities

With the local API server (`--local` flag):
- Upload files up to 2000 MB (2 GB)
- Download files of any size
- Faster file transfers
- Direct file access using local paths

## Support

If you encounter issues:

1. Check the server logs for error messages
2. Verify all credentials are correct
3. Ensure both server and bot are running
4. Test API connectivity with curl commands
5. Consult the official Telegram Bot API documentation