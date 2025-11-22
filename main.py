# This file serves as the entry point for Pella.app
# It imports and runs the actual Telegram bot application

import os
import logging
from telegram_download_bot import main

# Set up logging to see more details in the console
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

print("Starting Telegram File Download Bot...")
print(f"Bot token configured: {'Yes' if os.getenv('BOT_TOKEN') else 'No'}")
print(f"Environment: {os.environ.get('ENVIRONMENT', 'production')}")

if __name__ == '__main__':
    main()