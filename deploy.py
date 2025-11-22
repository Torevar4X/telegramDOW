"""
Deployment and Management Script for Telegram File Download Bot

This script handles:
1. Installing necessary dependencies
2. Setting up the local Telegram Bot API server (if needed)
3. Running the bot in different configurations
"""

import os
import sys
import subprocess
import platform
import time
import requests
import signal
import argparse
from pathlib import Path
import json


def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return False


def download_telegram_api_server():
    """Download the Telegram Bot API server if not already present"""
    
    # Determine OS and architecture
    os_name = platform.system().lower()
    arch = platform.machine().lower()
    
    # Construct download URL based on OS
    if os_name == "windows":
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-windows.zip"
        api_dir = "telegram-bot-api-windows"
        binary_name = "telegram-bot-api.exe"
    elif os_name == "linux":
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-linux"
        api_dir = "telegram-bot-api-linux"
        binary_name = "telegram-bot-api"
    elif os_name == "darwin":  # macOS
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-macos"
        api_dir = "telegram-bot-api-macos"
        binary_name = "telegram-bot-api"
    else:
        print(f"❌ Unsupported OS: {os_name}")
        return False
    
    print(f"⬇️ Downloading Telegram Bot API server for {os_name}...")
    
    # Create API directory if it doesn't exist
    api_path = Path("telegram-bot-api")
    api_path.mkdir(exist_ok=True)
    
    # Check if binary already exists
    binary_path = api_path / "bin" / binary_name
    if binary_path.exists():
        print("✅ Telegram Bot API server already exists!")
        return True
    
    try:
        import urllib.request
        import zipfile
        import tarfile
        
        # Download the file
        download_path = api_path / f"telegram-api-{os_name}.{'zip' if os_name == 'windows' else 'tar.gz'}"
        print(f"Downloading from: {url}")
        urllib.request.urlretrieve(url, download_path)
        
        # Extract the archive
        if os_name == "windows":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(api_path)
        else:
            with tarfile.open(download_path, 'r:gz') as tar_ref:
                tar_ref.extractall(api_path)
        
        # Move the binary to the expected location
        bin_dir = api_path / "bin"
        bin_dir.mkdir(exist_ok=True)
        
        # Find the binary and move it to bin directory
        for file_path in api_path.rglob(binary_name):
            if file_path.is_file():
                dest_path = bin_dir / binary_name
                file_path.rename(dest_path)
                print(f"✅ Telegram Bot API server installed to: {dest_path}")
                break
        else:
            print(f"❌ Could not find {binary_name} in the downloaded archive")
            return False
        
        # Make it executable on Unix systems
        if os_name != "windows":
            dest_path.chmod(0o755)
        
        return True
    except Exception as e:
        print(f"❌ Error downloading Telegram Bot API server: {e}")
        return False


def check_local_api_server():
    """Check if the local API server is running"""
    try:
        response = requests.get("http://localhost:8081", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def run_local_api_server(api_id=None, api_hash=None):
    """Start the local Telegram Bot API server in a subprocess"""
    if not api_id or not api_hash:
        print("⚠️  API credentials not provided. Using local API requires api_id and api_hash.")
        print("Get them from https://my.telegram.org")
        return None
    
    # Check if the server binary exists
    api_path = Path("telegram-bot-api") / "bin"
    if platform.system().lower() == "windows":
        binary_name = "telegram-bot-api.exe"
    else:
        binary_name = "telegram-bot-api"
    
    binary_path = api_path / binary_name
    if not binary_path.exists():
        print("❌ Telegram Bot API server not found. Attempting to download...")
        if not download_telegram_api_server():
            print("❌ Failed to download Telegram Bot API server")
            return None
    
    print(f"🚀 Starting local Telegram Bot API server on port 8081...")
    
    cmd = [
        str(binary_path),
        f"--api-id={api_id}",
        f"--api-hash={api_hash}",
        "--local",
        "--http-port=8081"
    ]
    
    try:
        process = subprocess.Popen(cmd)
        # Give the server a moment to start
        time.sleep(3)
        
        if check_local_api_server():
            print("✅ Local API server is running!")
            return process
        else:
            print("❌ Failed to start local API server")
            return None
    except Exception as e:
        print(f"❌ Error starting local API server: {e}")
        return None


def run_bot():
    """Run the Telegram Download Bot"""
    print("🤖 Starting Telegram Download Bot...")
    
    try:
        # Run the bot using the Python interpreter
        result = subprocess.run([sys.executable, "telegram_download_bot.py"])
        return result.returncode == 0
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        return False


def setup_config(api_id=None, api_hash=None, use_local_api=False):
    """Setup the API configuration file"""
    config = {
        "use_local_api": use_local_api,
        "local_api_url": "http://localhost:8081",
        "official_api_url": "https://api.telegram.org"
    }
    
    with open("api_config.json", "w") as f:
        json.dump(config, f, indent=2)
    
    print(f"⚙️  API configuration updated: use_local_api = {use_local_api}")


def main():
    parser = argparse.ArgumentParser(description="Deploy and manage Telegram File Download Bot")
    parser.add_argument("--bot-token", help="Telegram bot token")
    parser.add_argument("--api-id", help="Telegram API ID from my.telegram.org")
    parser.add_argument("--api-hash", help="Telegram API hash from my.telegram.org")
    parser.add_argument("--use-local-api", action="store_true", help="Use local API server")
    parser.add_argument("--setup-only", action="store_true", help="Only setup dependencies and API server")
    parser.add_argument("--run-bot", action="store_true", help="Run only the bot")
    parser.add_argument("--run-api", action="store_true", help="Run only the API server")
    
    args = parser.parse_args()
    
    # Set environment variables if provided
    if args.bot_token:
        os.environ["BOT_TOKEN"] = args.bot_token
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies. Exiting.")
        sys.exit(1)
    
    # If only setting up, download the API server and exit
    if args.setup_only:
        if args.use_local_api:
            if not download_telegram_api_server():
                print("❌ Failed to download Telegram Bot API server")
                sys.exit(1)
        print("✅ Setup completed!")
        return
    
    # Configure API settings
    use_local = args.use_local_api or (args.api_id and args.api_hash)
    setup_config(args.api_id, args.api_hash, use_local)
    
    # If running only the bot
    if args.run_bot:
        run_bot()
        return
    
    # If running only the API server
    if args.run_api:
        if not (args.api_id and args.api_hash):
            print("❌ API ID and API hash are required to run the API server")
            sys.exit(1)
        
        api_process = run_local_api_server(args.api_id, args.api_hash)
        if api_process:
            print("API server is running. Press Ctrl+C to stop.")
            try:
                api_process.wait()
            except KeyboardInterrupt:
                print("\nStopping API server...")
                api_process.terminate()
        return
    
    # Run both services
    api_process = None
    
    # Start local API server if configured
    if use_local and args.api_id and args.api_hash:
        api_process = run_local_api_server(args.api_id, args.api_hash)
        if not api_process:
            print("❌ Failed to start local API server, falling back to official API")
            setup_config(args.api_id, args.api_hash, False)  # Switch to official API
        else:
            print("⏳ Waiting for API server to be ready...")
            time.sleep(5)  # Give the server time to fully initialize
    
    # Run the bot
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
    finally:
        # Clean up API server process if it was started
        if api_process:
            api_process.terminate()
            print("🛑 API server stopped")


if __name__ == "__main__":
    main()