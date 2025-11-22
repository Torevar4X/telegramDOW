"""
Telegram File Download Bot
A robust bot for downloading and transferring large files (>4GB) from direct links.

Dependencies:
pip install python-telegram-bot aiohttp aiofiles validators

Usage:
1. Set your bot token in the BOT_TOKEN variable or as environment variable
2. Run: python bot.py
"""

import os
import asyncio
import logging
import time
import validators
import aiohttp
import aiofiles
from pathlib import Path
from urllib.parse import urlparse, unquote
from typing import Optional, Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

import os

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "7804137684:AAECd522V9bYDO64xN9HNqfaqEidG5yxuDk")  # Use environment variable or default
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

# Conversation states
WAITING_FOR_LINK, WAITING_FOR_FILENAME = range(2)

# User session data
user_sessions: Dict[int, dict] = {}


class FileDownloader:
    """Handles file downloading with progress tracking"""
    
    @staticmethod
    async def get_filename_from_url(url: str, session: aiohttp.ClientSession) -> Optional[str]:
        """Extract filename from URL or Content-Disposition header"""
        try:
            # Try HEAD request first to get headers without downloading
            async with session.head(url, allow_redirects=True, timeout=30) as response:
                # Check Content-Disposition header
                content_disposition = response.headers.get('Content-Disposition', '')
                if 'filename=' in content_disposition:
                    filename = content_disposition.split('filename=')[1].strip('"\'')
                    return unquote(filename)
                
                # Extract from URL path
                parsed_url = urlparse(str(response.url))
                filename = Path(unquote(parsed_url.path)).name
                
                if filename and filename != '':
                    return filename
                
                return None
        except Exception as e:
            logger.error(f"Error getting filename: {e}")
            return None
    
    @staticmethod
    async def get_file_size(url: str, session: aiohttp.ClientSession) -> Optional[int]:
        """Get file size from Content-Length header"""
        try:
            async with session.head(url, allow_redirects=True, timeout=30) as response:
                return int(response.headers.get('Content-Length', 0))
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return None
    
    @staticmethod
    async def download_file(
        url: str,
        filename: str,
        progress_callback=None
    ) -> Path:
        """Download file with progress tracking"""
        filepath = DOWNLOAD_DIR / filename
        
        # Configure timeout: no total timeout, but keep connection alive
        timeout = aiohttp.ClientTimeout(
            total=None,  # No total timeout
            connect=60,  # 60s to establish connection
            sock_read=300  # 5 minutes between chunks
        )
        
        connector = aiohttp.TCPConnector(
            limit=100,
            limit_per_host=30,
            ttl_dns_cache=300
        )
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.get(url, timeout=timeout) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: Failed to download file")
                
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                
                async with aiofiles.open(filepath, 'wb') as f:
                    async for chunk in response.content.iter_chunked(chunk_size):
                        await f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            await progress_callback(downloaded, total_size, progress)
        
        return filepath


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command"""
    welcome_message = (
        "🤖 <b>Welcome to File Download Bot!</b>\n\n"
        "I can download files from direct links and send them to you.\n"
        "I support files larger than 4GB!\n\n"
        "<b>Commands:</b>\n"
        "/download - Start downloading a file\n"
        "/cancel - Cancel current operation\n"
        "/help - Show this message\n\n"
        "Send me a direct download link to get started!"
    )
    await update.message.reply_text(welcome_message, parse_mode=ParseMode.HTML)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command"""
    await start(update, context)


async def validate_link(url: str) -> tuple[bool, str]:
    """Validate if URL is a valid direct download link"""
    # Basic URL validation
    if not validators.url(url):
        return False, "❌ Invalid URL format. Please provide a valid URL."
    
    # Check if it's HTTP/HTTPS
    if not url.startswith(('http://', 'https://')):
        return False, "❌ URL must start with http:// or https://"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True, timeout=30) as response:
                # Check if URL is accessible
                if response.status >= 400:
                    return False, f"❌ URL returned error code: {response.status}"
                
                # Check if it's a direct download (has content-length or content-disposition)
                content_type = response.headers.get('Content-Type', '')
                content_disposition = response.headers.get('Content-Disposition', '')
                content_length = response.headers.get('Content-Length', '')
                
                # If it has Content-Disposition or Content-Length, it's likely a direct link
                if content_disposition or content_length:
                    return True, "✅ Valid direct download link!"
                
                # Check if content-type is not HTML (likely a file)
                if 'text/html' not in content_type.lower():
                    return True, "✅ Valid direct download link!"
                
                return False, "❌ This doesn't appear to be a direct download link. It may be a web page."
                
    except asyncio.TimeoutError:
        return False, "❌ Connection timeout. Please check the URL and try again."
    except Exception as e:
        return False, f"❌ Error validating link: {str(e)}"


async def download_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /download command"""
    await update.message.reply_text(
        "📎 Please send me a direct download link.\n\n"
        "Example: https://example.com/file.zip"
    )
    return WAITING_FOR_LINK


async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle direct link submission"""
    user_id = update.effective_user.id
    url = update.message.text.strip()
    
    # Send validation message
    status_msg = await update.message.reply_text("🔍 Validating link...")
    
    # Validate the link
    is_valid, message = await validate_link(url)
    
    if not is_valid:
        await status_msg.edit_text(message)
        return WAITING_FOR_LINK
    
    # Get filename and file size
    try:
        async with aiohttp.ClientSession() as session:
            downloader = FileDownloader()
            filename = await downloader.get_filename_from_url(url, session)
            file_size = await downloader.get_file_size(url, session)
            
            if not filename:
                filename = "downloaded_file"
            
            # Store session data
            user_sessions[user_id] = {
                'url': url,
                'original_filename': filename,
                'file_size': file_size
            }
            
            # Format file size
            size_str = format_size(file_size) if file_size else "Unknown"
            
            # Create inline keyboard for options
            keyboard = [
                [InlineKeyboardButton("📄 Use Default Name", callback_data="default")],
                [InlineKeyboardButton("✏️ Rename File", callback_data="rename")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await status_msg.edit_text(
                f"✅ Link validated successfully!\n\n"
                f"<b>File Name:</b> <code>{filename}</code>\n"
                f"<b>File Size:</b> {size_str}\n\n"
                f"Choose an option:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.HTML
            )
            
            return WAITING_FOR_FILENAME
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)}")
        return WAITING_FOR_LINK


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        await query.edit_message_text("❌ Session expired. Please start over with /download")
        return ConversationHandler.END
    
    if query.data == "default":
        # Start download with original filename
        status_msg = await query.edit_message_text("⏳ Starting download...")
        await start_download(update, context, session['original_filename'], status_msg)
        return ConversationHandler.END
    
    elif query.data == "rename":
        # Ask for new filename
        await query.edit_message_text(
            f"✏️ Current filename: <code>{session['original_filename']}</code>\n\n"
            f"Please send the new filename (with extension):",
            parse_mode=ParseMode.HTML
        )
        return WAITING_FOR_FILENAME


async def handle_rename(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle filename rename"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        await update.message.reply_text("❌ Session expired. Please start over with /download")
        return ConversationHandler.END
    
    new_filename = update.message.text.strip()
    
    # Basic filename validation
    if not new_filename or '/' in new_filename or '\\' in new_filename:
        await update.message.reply_text("❌ Invalid filename. Please try again:")
        return WAITING_FOR_FILENAME
    
    status_msg = await update.message.reply_text("⏳ Starting download...")
    await start_download(update, context, new_filename, status_msg)
    
    return ConversationHandler.END


async def start_download(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    filename: str,
    status_msg=None
) -> None:
    """Start the file download and upload process"""
    user_id = update.effective_user.id
    session = user_sessions.get(user_id)
    
    if not session:
        return
    
    url = session['url']
    filepath = None
    
    try:
        # Progress callback for download
        last_progress = [0]  # Track last progress update
        last_update_time = [0]  # Track last update time

        async def progress_callback(downloaded, total, progress):
            current_time = time.time()
            current_progress = int(progress)

            # Update more frequently: every 2% or every 5 seconds
            should_update = False

            if total > 0:  # If we know the total size
                # Update every 2% at minimum
                progress_step = (current_progress // 2) * 2
                if progress_step != last_progress[0] and progress_step >= 2:
                    should_update = True
                    last_progress[0] = progress_step
            else:  # If total size is unknown, update more frequently based on data downloaded
                if downloaded > (last_progress[0] + 10 * 1024 * 1024):  # Every 10MB
                    should_update = True
                    last_progress[0] = downloaded

            # Also update if enough time has passed (5 seconds) to ensure UI responsiveness
            if current_time - last_update_time[0] >= 5:
                should_update = True
                if total > 0:
                    last_progress[0] = current_progress  # Update to current progress to avoid duplicate updates
                else:
                    last_progress[0] = downloaded

            if should_update:
                last_update_time[0] = current_time
                size_downloaded = format_size(downloaded)
                size_total = format_size(total) if total > 0 else "Unknown"

                # Create animated progress bar
                if total > 0:
                    progress_bar = create_progress_bar(current_progress)
                    progress_text = f"{current_progress}%"
                else:
                    progress_bar = create_progress_bar(0)  # Show empty bar when total is unknown
                    progress_text = "Unknown"

                if status_msg:
                    try:
                        await status_msg.edit_text(
                            f"⬇️ <b>Downloading...</b>\n\n"
                            f"{progress_bar} {progress_text}\n\n"
                            f"📦 {size_downloaded} / {size_total}",
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as e:
                        pass  # Ignore "message not modified" errors
        
        # Download file
        downloader = FileDownloader()
        filepath = await downloader.download_file(url, filename, progress_callback)
        
        # Get file size
        file_size = filepath.stat().st_size
        chat_id = update.effective_chat.id
        
        # Check Telegram's file size limit (2GB for bots)
        MAX_TELEGRAM_SIZE = 2 * 1024 * 1024 * 1024  # 2GB
        
        if file_size > MAX_TELEGRAM_SIZE:
            error_msg = (
                f"❌ <b>File exceeds Telegram's limit!</b>\n\n"
                f"📦 <b>File size:</b> {format_size(file_size)}\n"
                f"⚠️ <b>Telegram limit:</b> 2 GB\n\n"
                f"💡 <b>Solutions:</b>\n"
                f"• Use a file compression tool\n"
                f"• Split the file into smaller parts\n"
                f"• Upload to cloud storage (Google Drive, Mega, etc.)"
            )
            if status_msg:
                await status_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=error_msg,
                    parse_mode=ParseMode.HTML
                )
            return
        
        if status_msg:
            await status_msg.edit_text(
                f"📤 <b>Uploading to Telegram...</b>\n\n"
                f"📦 {format_size(file_size)}\n"
                f"⏳ Please wait, this may take several minutes...",
                parse_mode=ParseMode.HTML
            )
        
        # Upload with retry logic and progress animation
        max_retries = 3
        retry_count = 0
        upload_success = False
        upload_start_time = asyncio.get_event_loop().time()
        
        # Start upload progress animation task
        upload_animation_task = None
        animation_active = [True]  # Use list for mutable flag
        
        async def animate_upload_progress():
            """Animate upload progress with a spinner"""
            frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
            frame_idx = 0
            last_update = 0
            
            while animation_active[0]:
                elapsed = int(asyncio.get_event_loop().time() - upload_start_time)
                minutes = elapsed // 60
                seconds = elapsed % 60
                
                # Update every 2 seconds to avoid rate limits
                if elapsed - last_update >= 2:
                    last_update = elapsed
                    frame_idx = (frame_idx + 1) % len(frames)
                    
                    if status_msg:
                        try:
                            await status_msg.edit_text(
                                f"📤 <b>Uploading to Telegram...</b>\n\n"
                                f"{frames[frame_idx]} <b>In Progress</b>\n\n"
                                f"📦 Size: {format_size(file_size)}\n"
                                f"⏱️ Time: {minutes:02d}:{seconds:02d}\n\n"
                                f"⏳ Please wait, do not close the bot...",
                                parse_mode=ParseMode.HTML
                            )
                        except Exception:
                            pass
                
                await asyncio.sleep(1)
        
        while retry_count < max_retries and not upload_success:
            try:
                # Start animation task
                if status_msg:
                    animation_active[0] = True
                    upload_animation_task = asyncio.create_task(animate_upload_progress())
                
                # Calculate dynamic timeouts based on file size
                # Assume minimum upload speed of 100KB/s (conservative)
                estimated_time = file_size / (100 * 1024)
                timeout_buffer = 600  # 10 minute buffer
                
                read_timeout = min(estimated_time + timeout_buffer, 7200)  # Max 2 hours
                write_timeout = min(estimated_time + timeout_buffer, 7200)
                
                with open(filepath, 'rb') as f:
                    await context.bot.send_document(
                        chat_id=chat_id,
                        document=f,
                        filename=filename,
                        caption=f"✅ File uploaded successfully!\n📦 Size: {format_size(file_size)}",
                        read_timeout=read_timeout,
                        write_timeout=write_timeout,
                        connect_timeout=60,
                        pool_timeout=60
                    )
                
                # Stop animation
                animation_active[0] = False
                if upload_animation_task:
                    await upload_animation_task
                
                upload_success = True
                if status_msg:
                    await status_msg.delete()
                
            except Exception as upload_error:
                # Stop animation on error
                animation_active[0] = False
                if upload_animation_task:
                    try:
                        await upload_animation_task
                    except:
                        pass
                
                retry_count += 1
                error_type = type(upload_error).__name__
                
                if retry_count < max_retries:
                    wait_time = retry_count * 10  # 10, 20, 30 seconds
                    logger.warning(f"Upload attempt {retry_count} failed: {error_type}. Retrying in {wait_time}s...")
                    
                    if status_msg:
                        try:
                            await status_msg.edit_text(
                                f"⚠️ <b>Upload Interrupted</b>\n\n"
                                f"Error: {error_type}\n\n"
                                f"🔄 Retrying... (Attempt {retry_count + 1}/{max_retries})\n"
                                f"⏳ Waiting {wait_time} seconds...",
                                parse_mode=ParseMode.HTML
                            )
                        except Exception:
                            pass
                    
                    await asyncio.sleep(wait_time)
                    
                    # Reset timer for next attempt
                    upload_start_time = asyncio.get_event_loop().time()
                else:
                    raise upload_error  # Re-raise if all retries failed
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = f"❌ <b>Upload Failed</b>\n\n"
        
        # Categorize errors and provide specific guidance
        if "NetworkError" in error_type or "ReadError" in error_type or "WriteError" in error_type:
            error_msg += (
                f"⚠️ <b>Network connection issue</b>\n\n"
                f"The upload was interrupted due to network problems.\n\n"
                f"💡 <b>Possible causes:</b>\n"
                f"• Unstable internet connection\n"
                f"• File is very large ({format_size(file_size) if filepath and filepath.exists() else 'unknown'})\n"
                f"• Server connectivity issues\n\n"
                f"🔄 <b>Please try:</b>\n"
                f"• Check your internet connection\n"
                f"• Try again during off-peak hours\n"
                f"• Use a wired connection if possible\n"
                f"• Try a smaller file first to test"
            )
        elif "Timed out" in str(e) or "timeout" in str(e).lower():
            error_msg += (
                f"⚠️ <b>Upload timeout</b>\n\n"
                f"The file took too long to upload.\n\n"
                f"💡 <b>Suggestions:</b>\n"
                f"• Your upload speed may be slow\n"
                f"• Try during better network conditions\n"
                f"• Consider using a smaller file"
            )
        else:
            error_msg += f"<code>{error_type}: {str(e)}</code>\n\n"
            error_msg += "Please try again or contact support."
        
        if status_msg:
            await status_msg.edit_text(error_msg, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_msg,
                parse_mode=ParseMode.HTML
            )
        logger.error(f"Download/Upload error: {e}", exc_info=True)
    
    finally:
        # Cleanup: Delete downloaded file
        if filepath and filepath.exists():
            try:
                filepath.unlink()
                logger.info(f"Deleted file: {filepath}")
            except Exception as e:
                logger.error(f"Error deleting file: {e}")
        
        # Clear user session
        if user_id in user_sessions:
            del user_sessions[user_id]


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel current operation"""
    user_id = update.effective_user.id
    if user_id in user_sessions:
        del user_sessions[user_id]
    
    await update.message.reply_text(
        "❌ Operation cancelled. Send /download to start again."
    )
    return ConversationHandler.END


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable size"""
    if not size_bytes:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def create_progress_bar(progress: int, length: int = 15) -> str:
    """Create an animated progress bar"""
    filled = int(length * progress / 100)
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}]"


def main() -> None:
    """Start the bot"""
    if BOT_TOKEN == "7804137684:AAECd522V9bYDO64xN9HNqfaqEidG5yxuDk" or not BOT_TOKEN:
        print("❌ Error: Please set your bot token as an environment variable")
        return

    # Create application with configurable API server
    # On hosting platforms like Pella.app, use official API by default
    import json
    try:
        with open('api_config.json', 'r') as config_file:
            config = json.load(config_file)
            if config.get('use_local_api', False):  # Changed default to False for hosting
                # For local API, construct the full base URL with bot prefix
                base_url = f"{config.get('local_api_url', 'http://localhost:8081')}/bot"
                print(f"[INFO] Using local API server: {base_url}")
            else:
                # For official API, construct the full base URL with bot prefix
                base_url = f"{config.get('official_api_url', 'https://api.telegram.org')}/bot"
                print(f"[INFO] Using official API server: {base_url}")
        application = Application.builder().token(BOT_TOKEN).base_url(base_url).build()
    except FileNotFoundError:
        # Fallback to official API if config file doesn't exist
        base_url = "https://api.telegram.org/bot"
        print(f"[INFO] Using official API server: {base_url}")
        application = Application.builder().token(BOT_TOKEN).base_url(base_url).build()
    
    # Conversation handler for download process
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('download', download_command),
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
        ],
        states={
            WAITING_FOR_LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link)
            ],
            WAITING_FOR_FILENAME: [
                CallbackQueryHandler(button_callback),
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_rename)
            ]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(conv_handler)
    
    # Start bot
    print("[BOT] Bot started successfully!")
    print("Press Ctrl+C to stop")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()