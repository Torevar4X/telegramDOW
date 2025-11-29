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


def build_telegram_api_server():
    """Build the Telegram Bot API server from source"""
    import subprocess
    import os

    # Determine OS
    os_name = platform.system().lower()

    if os_name != "linux":
        print(f"❌ Building from source is only supported on Linux. Current OS: {os_name}")
        return False

    print("🔨 Building Telegram Bot API server from source...")

    # Create API directory if it doesn't exist
    api_path = Path("telegram-bot-api-source")
    api_path.mkdir(exist_ok=True)

    # Check if already built
    binary_path = api_path / "inst" / "bin" / "telegram-bot-api"
    if binary_path.exists():
        print("✅ Telegram Bot API server already built!")
        # Copy to expected location
        expected_path = Path("telegram-bot-api") / "bin" / "telegram-bot-api"
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy2(binary_path, expected_path)
        expected_path.chmod(0o755)
        return True

    try:
        # Run the build commands
        build_dir = api_path / "build"
        source_dir = api_path

        print("📦 Cloning telegram-bot-api repository...")
        result = subprocess.run([
            "git", "clone", "--recursive", "https://github.com/tdlib/telegram-bot-api.git", str(source_dir)
        ], capture_output=True, text=True, timeout=300)  # 5 minute timeout

        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return False

        print("🔧 Creating build directory...")
        build_dir.mkdir(exist_ok=True)

        print("⚙️ Running cmake configuration...")
        result = subprocess.run([
            "cmake", "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_INSTALL_PREFIX=../inst", ".."
        ], cwd=build_dir, capture_output=True, text=True, timeout=300)

        if result.returncode != 0:
            print(f"❌ CMake configuration failed: {result.stderr}")
            return False

        print("🏗️ Building the project...")
        result = subprocess.run([
            "cmake", "--build", ".", "--target", "install"
        ], cwd=build_dir, capture_output=True, text=True, timeout=1800)  # 30 minute timeout

        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False

        print("✅ Build completed successfully!")

        # Copy to expected location
        expected_path = Path("telegram-bot-api") / "bin" / "telegram-bot-api"
        expected_path.parent.mkdir(parents=True, exist_ok=True)
        import shutil
        if binary_path.exists():
            shutil.copy2(binary_path, expected_path)
            expected_path.chmod(0o755)
            print(f"✅ Telegram Bot API server installed to: {expected_path}")
            return True
        else:
            print(f"❌ Expected binary not found at {binary_path}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Build process timed out")
        return False
    except Exception as e:
        print(f"❌ Error building Telegram Bot API server: {e}")
        return False


def download_telegram_api_server():
    """Download or build the Telegram Bot API server if not already present"""
    import subprocess

    # Determine OS and architecture
    os_name = platform.system().lower()

    print(f"📦 Setting up Telegram Bot API server for {os_name}...")

    # Create API directory if it doesn't exist
    api_path = Path("telegram-bot-api")
    api_path.mkdir(exist_ok=True)

    # Check if binary already exists
    binary_path = api_path / "bin" / "telegram-bot-api"
    if binary_path.exists():
        print("✅ Telegram Bot API server already exists!")
        return True

    # Try building from source first (for Linux environments like Pella)
    if os_name == "linux":
        print(" attempting to build from source...")
        if build_telegram_api_server():
            return True
        else:
            print("⚠️ Building from source failed, trying download approach...")

    # Construct download URL based on OS
    if os_name == "windows":
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-windows.zip"
        binary_name = "telegram-bot-api.exe"
    elif os_name == "linux":
        # Try to get the correct Linux binary from GitHub releases
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
                    asset_name_lower = asset["name"].lower()
                    if ("linux" in asset_name_lower and
                        "static" in asset_name_lower and
                        "tar.gz" in asset_name_lower):
                        linux_asset = asset["browser_download_url"]
                        break

                # If no static build found, try to find any linux binary
                if not linux_asset:
                    for asset in assets:
                        asset_name_lower = asset["name"].lower()
                        if "linux" in asset_name_lower and not "debug" in asset_name_lower:
                            linux_asset = asset["browser_download_url"]
                            break

                if linux_asset:
                    url = linux_asset
                else:
                    # Fallback if no Linux asset is found
                    print("❌ No suitable Linux binary found in GitHub releases")
                    return False
            else:
                # If GitHub API request fails
                print("❌ Could not fetch release info from GitHub")
                return False
        except Exception as e:
            # If there's an error getting the release info
            print(f"❌ Error fetching release info: {e}")
            return False

        binary_name = "telegram-bot-api"  # Override to use the standard name after extraction
    elif os_name == "darwin":  # macOS
        url = "https://github.com/tdlib/telegram-bot-api/releases/latest/download/telegram-bot-api-macos"
        binary_name = "telegram-bot-api"
    else:
        print(f"❌ Unsupported OS: {os_name}")
        return False

    print(f"⬇️ Downloading Telegram Bot API server for {os_name}...")

    # Check if binary already exists (after build attempt)
    if binary_path.exists():
        print("✅ Telegram Bot API server already exists!")
        return True

    try:
        import urllib.request
        import zipfile
        import tarfile

        # Determine the extension for the downloaded file
        if os_name == "windows":
            download_ext = ".zip"
        elif "tar.gz" in url.lower():
            download_ext = ".tar.gz"
        elif "tar.xz" in url.lower():
            download_ext = ".tar.xz"
        else:
            # For Linux, the binary might be directly downloadable
            download_ext = ""

        download_path = api_path / f"telegram-api-{os_name}{download_ext}"
        print(f"Downloading from: {url}")
        urllib.request.urlretrieve(url, download_path)

        # Extract the archive or handle the binary
        if os_name == "windows":
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(api_path)
        else:
            # For Linux and macOS, determine if the download is an archive or binary
            if is_binary_file(download_path) and os_name != "windows":
                # If it's already a binary executable, copy it directly to the bin directory
                bin_dir = api_path / "bin"
                bin_dir.mkdir(exist_ok=True)
                dest_path = bin_dir / "telegram-bot-api"  # Use standard name
                import shutil
                shutil.move(download_path, dest_path)
                print(f"✅ Telegram Bot API server installed to: {dest_path}")

                # Make it executable on Unix systems
                dest_path.chmod(0o755)

                return True
            else:
                # It's an archive, so extract it
                if download_ext == ".tar.gz":
                    import tarfile
                    with tarfile.open(download_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(api_path)
                elif download_ext == ".tar.xz":
                    import tarfile
                    with tarfile.open(download_path, 'r:xz') as tar_ref:
                        tar_ref.extractall(api_path)
                elif download_ext == ".zip":
                    with zipfile.ZipFile(download_path, 'r') as zip_ref:
                        zip_ref.extractall(api_path)

                # Find the binary file in the extracted content and move it to bin
                bin_dir = api_path / "bin"
                bin_dir.mkdir(exist_ok=True)

                # Look for the telegram-bot-api binary in the extracted files
                for file_path in api_path.rglob("*"):
                    if file_path.is_file() and "telegram-bot-api" in file_path.name and not file_path.name.endswith(('.tar.gz', '.zip', '.tar.xz')):
                        dest_path = bin_dir / "telegram-bot-api"
                        file_path.rename(dest_path)
                        print(f"✅ Telegram Bot API server installed to: {dest_path}")

                        # Make it executable on Unix systems
                        dest_path.chmod(0o755)

                        return True

                print(f"❌ Could not find telegram-bot-api binary in the extracted files")
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
    
    # If API credentials are provided, try to start local API server
    if api_id and api_hash:
        print(f"✅ Using local API with provided credentials")

        # Start the local API server in a subprocess
        api_process = run_local_api_server(api_id, api_hash)
        if not api_process:
            print("⚠️  Local API server setup failed, falling back to official API")
            print("💡 This is normal on some hosting platforms that restrict additional processes")
            print("   Your bot will still work but with standard Telegram file size limits (50-100MB)")
            setup_config(use_local_api=False)

            # Run the bot with official API
            try:
                run_bot()
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
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
        print("ℹ️  No API credentials provided, using official Telegram API")
        print("   File size limit: 50-100MB")

        setup_config(use_local_api=False)

        # Run the bot
        try:
            run_bot()
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")


if __name__ == "__main__":
    main()