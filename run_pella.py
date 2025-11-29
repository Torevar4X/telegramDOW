"""
Deployment script for running Telegram Download Bot on Pella platform.

This script starts both the local Telegram Bot API server and the bot itself
using a single Python file, as required by Pella which only supports Python
execution (not batch or shell files).
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
import asyncio
import threading
from telegram_download_bot import main as run_bot


def download_telegram_api_server():
    """Download the Telegram Bot API server if not already present"""

    # Determine OS and architecture
    os_name = platform.system().lower()
    arch = platform.machine().lower()

    # Construct download URL based on OS
    if os_name == "windows":
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-windows.zip"
        binary_name = "telegram-bot-api.exe"
    elif os_name == "linux":
        # Pella runs on Linux - checking latest release for the Linux binary
        try:
            import requests
            # Get the latest release info from GitHub
            response = requests.get("https://api.github.com/repos/tdlib/telegram-bot-api/releases/latest")
            if response.status_code == 200:
                release = response.json()
                # Find the asset for Linux
                assets = release.get("assets", [])
                linux_asset = None
                for asset in assets:
                    # Look for assets that match linux and are not debug builds
                    if "linux" in asset["name"].lower() and "static" in asset["name"].lower():
                        linux_asset = asset["browser_download_url"]
                        break

                # If no static build found, try to find any linux binary
                if not linux_asset:
                    for asset in assets:
                        if "linux" in asset["name"].lower():
                            linux_asset = asset["browser_download_url"]
                            break

                if linux_asset:
                    url = linux_asset
                else:
                    # Fallback to a known URL pattern if no specific asset found
                    url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-linux"
            else:
                # If GitHub API request fails, use the generic URL
                url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-linux"
        except Exception:
            # If there's an error getting the release info, use the generic URL
            url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-linux"

        binary_name = "telegram-bot-api"
    elif os_name == "darwin":  # macOS
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-macos"
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
        download_path = api_path / f"telegram-api-{os_name}.{'zip' if os_name == 'windows' else '.tar.gz'}"
        print(f"Downloading from: {url}")
        urllib.request.urlretrieve(url, download_path)

        # Extract the archive
        if os_name == "windows":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(api_path)
        else:
            # For Linux and macOS, the download is usually a binary file, not an archive
            # So we should check if the downloaded file is the binary itself
            if is_binary_file(download_path):
                # If it's already a binary, copy it directly to the bin directory
                bin_dir = api_path / "bin"
                bin_dir.mkdir(exist_ok=True)
                dest_path = bin_dir / binary_name
                import shutil
                shutil.move(download_path, dest_path)
                print(f"✅ Telegram Bot API server installed to: {dest_path}")

                # Make it executable on Unix systems
                if os_name != "windows":
                    dest_path.chmod(0o755)

                return True
            else:
                # If it's an archive, extract it
                import tarfile
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

                        # Make it executable on Unix systems
                        if os_name != "windows":
                            dest_path.chmod(0o755)

                        break
                else:
                    print(f"❌ Could not find {binary_name} in the downloaded archive")
                    return False

        return True
    except Exception as e:
        print(f"❌ Error downloading Telegram Bot API server: {e}")
        return False


def is_binary_file(file_path):
    """Check if a file is a binary executable"""
    try:
        with open(file_path, 'rb') as f:
            chunk = f.read(1024)
            # Check for common binary file signatures (magic numbers)
            if chunk.startswith(b'\x7fELF'):  # ELF (Linux Executable)
                return True
            if chunk.startswith(b'MZ'):       # DOS/Windows Executable
                return True
        return False
    except:
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
        # For Pella, we assume Linux
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
        # On Linux (Pella), we need to handle the process differently
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Give the server a moment to start
        time.sleep(5)

        if check_local_api_server():
            print("✅ Local API server is running!")
            return process
        else:
            print("❌ Failed to start local API server")
            # Print any error messages from the process
            try:
                stdout, stderr = process.communicate(timeout=1)
                print(f"Server stdout: {stdout.decode()}")
                print(f"Server stderr: {stderr.decode()}")
            except subprocess.TimeoutExpired:
                process.kill()
            return None
    except Exception as e:
        print(f"❌ Error starting local API server: {e}")
        return None


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


def run_bot_with_local_api():
    """Run the bot with local API configuration"""
    # Setup config to use local API
    api_id = os.getenv("API_ID", os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("API_HASH", os.getenv("TELEGRAM_API_HASH"))
    
    if not api_id or not api_hash:
        print("⚠️  API credentials not found in environment variables.")
        print("Make sure you have set API_ID and API_HASH environment variables.")
        print("Falling back to official API...")
        setup_config(use_local_api=False)
    else:
        setup_config(api_id, api_hash, use_local_api=True)
    
    # Run the bot
    try:
        run_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        return True
    except Exception as e:
        print(f"❌ Error running bot: {e}")
        return False


def main():
    print("🚀 Starting Telegram Download Bot for Pella deployment")
    print("=====================================================")
    
    # Get credentials from environment variables
    api_id = os.getenv("API_ID", os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("API_HASH", os.getenv("TELEGRAM_API_HASH"))
    bot_token = os.getenv("BOT_TOKEN", os.getenv("TELEGRAM_BOT_TOKEN"))
    
    # Check if required environment variables are set
    if not bot_token:
        print("❌ Error: BOT_TOKEN environment variable not set")
        print("Please set your BOT_TOKEN environment variable")
        sys.exit(1)
    
    # Set the bot token in environment for the bot script to use
    os.environ["BOT_TOKEN"] = bot_token
    
    # If API credentials are provided, start local API server
    if api_id and api_hash:
        print(f"✅ Using local API with provided credentials")
        
        # Start the local API server in a subprocess
        api_process = run_local_api_server(api_id, api_hash)
        if not api_process:
            print("❌ Failed to start local API server, falling back to official API")
            setup_config(use_local_api=False)
        else:
            print("⏳ Waiting for API server to be ready...")
            time.sleep(5)  # Give the server time to fully initialize
            
            # Run the bot in the main thread
            try:
                run_bot_with_local_api()
            except KeyboardInterrupt:
                print("\n🛑 Stopping services...")
            finally:
                # Clean up API server process
                if api_process:
                    api_process.terminate()
                    print("🛑 API server stopped")
    else:
        # Run without local API server (using official API)
        print("⚠️  API credentials not provided, using official Telegram API")
        print("This limits file size to 50MB-100MB instead of 2GB+ with local API")
        
        setup_config(use_local_api=False)
        
        # Run the bot
        try:
            run_bot()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")


if __name__ == "__main__":
    main()