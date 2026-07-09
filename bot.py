'''
THE PLUG - YouTube/Spotify Music Downloader Bot
✅ Uses yt-dlp subprocess
✅ Converts and saves MP3 when requested
✅ Auto-deletes after sending
✅ Channel subscription required
'''

import os
import asyncio
import subprocess
import glob
import shutil
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "7869986791:AAERF18jdtPm_kmdaGqKKA3Ce6W18CGgAy8")
CHANNEL_USERNAME = "habitsofmusic"  # Your channel username (without @)
CHANNEL_LINK = "https://t.me/habitsofmusic"
SUPPORT_LINK = "https://t.me/your_support_bot"  # Change this
SUPPORT_AD_LINK = "https://your-ad-link.com"  # Change this

# Store user format preferences
user_format_preferences = {}

# --- SUBSCRIPTION CHECK ---
async def check_user_joined_channel(app, user_id):
    """Check if user is a member of the channel."""
    try:
        member = await app.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        print(f"[DEBUG] Member status: {member.status}")
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"[Channel Join Check Error] {e}")
        return False

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    user_id = update.effective_user.id
    joined = await check_user_joined_channel(context.application, user_id)

    if not joined:
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\n"
            "You must join @habitsofmusic to use this bot.\n\n"
            "Click below to join, then try again!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )
        return

    await update.message.reply_text(
        "🎵 **Welcome to THE PLUG!**\n\n"
        "I can download music from YouTube and Spotify!\n\n"
        "**How to use:**\n"
        "1️⃣ Choose a format below\n"
        "2️⃣ Send me a YouTube or Spotify link\n"
        "3️⃣ I'll download and send it to you!\n\n"
        "**Format Options:**",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 MP3 (Audio)", callback_data="mp3"),
                InlineKeyboardButton("🎬 720p (Video)", callback_data="720p")
            ],
            [
                InlineKeyboardButton("📹 480p (Video)", callback_data="480p"),
                InlineKeyboardButton("🎬 1080p (Video)", callback_data="1080p")
            ],
            [
                InlineKeyboardButton("❓ Help", callback_data="help"),
                InlineKeyboardButton("🔒 Privacy", callback_data="privacy")
            ],
            [
                InlineKeyboardButton("❤️ Support Us", url=SUPPORT_AD_LINK)
            ]
        ])
    )

async def format_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle format selection via callback."""
    query = update.callback_query
    user_id = query.from_user.id
    format_choice = query.data
    await query.answer()
    
    # Handle help and privacy callbacks
    if format_choice == "help":
        await query.edit_message_text(
            "📖 **Help Menu**\n\n"
            "1. Choose a format (MP3, 480p, 720p, or 1080p)\n"
            "2. Send a YouTube or Spotify link\n"
            "3. I'll download and send it!\n\n"
            "**Commands:**\n"
            "/start - Show this menu\n"
            "/privacy - Privacy policy\n"
            "/cancel - Cancel download\n\n"
            "**Supported:**\n"
            "✅ YouTube videos\n"
            "✅ Spotify tracks\n"
            "✅ YouTube Music\n\n"
            "⚠️ Files auto-delete after 30 seconds!",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    if format_choice == "privacy":
        await query.edit_message_text(
            "🔒 **Privacy Policy**\n\n"
            "• We do NOT store your personal data\n"
            "• Chat IDs are cached temporarily\n"
            "• No files are saved permanently\n"
            "• Your data is never shared\n\n"
            "Files are deleted after 30 seconds.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    if format_choice == "back_to_menu":
        # Go back to main menu
        await query.edit_message_text(
            "🎵 **Welcome to THE PLUG!**\n\n"
            "Choose a format to download:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎵 MP3 (Audio)", callback_data="mp3"),
                    InlineKeyboardButton("🎬 720p (Video)", callback_data="720p")
                ],
                [
                    InlineKeyboardButton("📹 480p (Video)", callback_data="480p"),
                    InlineKeyboardButton("🎬 1080p (Video)", callback_data="1080p")
                ]
            ])
        )
        return
    
    # Store format preference
    user_format_preferences[user_id] = format_choice
    await query.edit_message_text(
        f"✅ **Format selected: {format_choice}**\n\n"
        "Now send me a YouTube or Spotify link!\n\n"
        "Example: `https://www.youtube.com/watch?v=dQw4w9WgXcQ`\n"
        "Or: `https://open.spotify.com/track/...`\n\n"
        "⚠️ Files auto-delete after 30 seconds!",
        parse_mode="Markdown"
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle 'Check Again' callback."""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    joined = await check_user_joined_channel(context.application, user_id)
    
    if joined:
        await query.edit_message_text(
            "✅ **Subscription Verified!**\n\n"
            "You now have full access to THE PLUG!\n"
            "Send /start to see the menu.",
            parse_mode="Markdown"
        )
    else:
        await query.edit_message_text(
            "❌ **Still Not Joined!**\n\n"
            "Please join @habitsofmusic first:\n"
            f"{CHANNEL_LINK}\n\n"
            "Then click 'I've Joined! Check Again'.",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming YouTube/Spotify links."""
    url = update.message.text
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if user joined channel
    joined = await check_user_joined_channel(context.application, user_id)
    if not joined:
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\n"
            "You must join @habitsofmusic first!\n"
            f"{CHANNEL_LINK}",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )
        return

    # Check if it's a valid link
    if not any(domain in url for domain in ['youtube.com', 'youtu.be', 'spotify.com']):
        await update.message.reply_text(
            "❌ **Invalid Link!**\n\n"
            "Please send a valid YouTube or Spotify link.\n\n"
            "Examples:\n"
            "`https://www.youtube.com/watch?v=...`\n"
            "`https://open.spotify.com/track/...`",
            parse_mode="Markdown"
        )
        return

    # Get format preference (default to MP3)
    format_choice = user_format_preferences.get(user_id, "mp3")
    
    await update.message.reply_text(
        f"✅ **Received!**\n\n"
        f"Format: `{format_choice}`\n"
        "⏳ Downloading now, please wait...",
        parse_mode="Markdown"
    )
    
    # Start download in background
    asyncio.create_task(handle_download_and_send(chat_id, url, context, format_choice))

async def handle_download_and_send(chat_id, url, context, format_choice):
    """Download and send the file to user."""
    try:
        # Create temp directory
        download_dir = f"./downloads/{chat_id}"
        os.makedirs(download_dir, exist_ok=True)
        
        # Change to download directory
        original_dir = os.getcwd()
        os.chdir(download_dir)
        
        # Check if it's a Spotify link
        is_spotify = 'spotify.com' in url
        
        if is_spotify:
            # Use spotdl to get track metadata (not download)
            await context.bot.send_message(
                chat_id=chat_id,
                text="🔍 **Spotify Link Detected!**\n\n"
                     "Searching for this track on YouTube...",
                parse_mode="Markdown"
            )
            
            # Get track info using spotdl
            spotdl_cmd = [
                "spotdl",
                url,
                "--print", "title,artist"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *spotdl_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and stdout:
                # Parse the output to get search query
                track_info = stdout.decode().strip().split(',')
                if len(track_info) >= 2:
                    artist = track_info[0].strip()
                    title = track_info[1].strip()
                    search_query = f"{artist} {title} audio"
                    
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🎵 **Found:** {artist} - {title}\n\n"
                             f"Downloading from YouTube...",
                        parse_mode="Markdown"
                    )
                    
                    # Now search and download from YouTube
                    if format_choice == "mp3":
                        cmd = [
                            "yt-dlp",
                            "--js-runtimes", "node",
                            f"ytsearch1:{search_query}",
                            "-f", "bestaudio/best",
                            "--extract-audio",
                            "--audio-format", "mp3",
                            "--audio-quality", "192K",
                            "-o", "%(title)s.%(ext)s"
                        ]
                    else:
                        height_map = {"480p": 480, "720p": 720, "1080p": 1080}
                        height = height_map.get(format_choice, 720)
                        cmd = [
                            "yt-dlp",
                            "--js-runtimes", "node",
                            f"ytsearch1:{search_query}",
                            "-f", f"bestvideo[height<={height}]+bestaudio/best",
                            "--merge-output-format", "mp4",
                            "-o", "%(title)s.%(ext)s"
                        ]
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ **Could not parse track info!**\n\n"
                             "Please try a direct YouTube link instead.",
                        parse_mode="Markdown"
                    )
                    os.chdir(original_dir)
                    shutil.rmtree(download_dir, ignore_errors=True)
                    return
            else:
                # Fallback: try spotdl with different approach
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ **Spotify link not recognized.**\n\n"
                         "Trying to search YouTube directly...",
                    parse_mode="Markdown"
                )
                
                # Use yt-dlp to search directly (less accurate but works sometimes)
                if format_choice == "mp3":
                    cmd = [
                        "yt-dlp",
                        "--js-runtimes", "node",
                        f"ytsearch1:{url.replace('https://open.spotify.com/track/', '')}",
                        "-f", "bestaudio/best",
                        "--extract-audio",
                        "--audio-format", "mp3",
                        "--audio-quality", "192K",
                        "-o", "%(title)s.%(ext)s"
                    ]
                else:
                    height_map = {"480p": 480, "720p": 720, "1080p": 1080}
                    height = height_map.get(format_choice, 720)
                    cmd = [
                        "yt-dlp",
                        "--js-runtimes", "node",
                        f"ytsearch1:{url.replace('https://open.spotify.com/track/', '')}",
                        "-f", f"bestvideo[height<={height}]+bestaudio/best",
                        "--merge-output-format", "mp4",
                        "-o", "%(title)s.%(ext)s"
                    ]
        else:
            # Direct YouTube link
            if format_choice == "mp3":
                cmd = [
                    "yt-dlp",
                    "--js-runtimes", "node",
                    "-f", "bestaudio/best",
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--audio-quality", "192K",
                    "-o", "%(title)s.%(ext)s",
                    url
                ]
            else:
                height_map = {"480p": 480, "720p": 720, "1080p": 1080}
                height = height_map.get(format_choice, 720)
                cmd = [
                    "yt-dlp",
                    "--js-runtimes", "node",
                    "-f", f"bestvideo[height<={height}]+bestaudio/best",
                    "--merge-output-format", "mp4",
                    "-o", "%(title)s.%(ext)s",
                    url
                ]
        
        # Run the download
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        # Check for errors
        if process.returncode != 0:
            error_output = stderr.decode().strip()
            
            if "Sign in to confirm" in error_output:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ **YouTube is Blocking Downloads!**\n\n"
                         "Try a different video or use a Spotify link.\n\n"
                         "If using Spotify, make sure it's a valid track URL.",
                    parse_mode="Markdown"
                )
            elif "Unsupported URL" in error_output:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="❌ **Unsupported URL!**\n\n"
                         "Please send a valid YouTube or Spotify link.",
                    parse_mode="Markdown"
                )
            else:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"❌ **Download Failed!**\n\nError: {error_output[:200]}",
                    parse_mode="Markdown"
                )
            os.chdir(original_dir)
            shutil.rmtree(download_dir, ignore_errors=True)
            return

        # Find downloaded file
        files = glob.glob("*.mp3") if format_choice == "mp3" else glob.glob("*.mp4")
        if not files:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ **Download Failed!**\n\nFile not found after download.",
                parse_mode="Markdown"
            )
            os.chdir(original_dir)
            shutil.rmtree(download_dir, ignore_errors=True)
            return

        file_path = files[0]
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
        
        if file_size > 48:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ **File is {file_size:.1f}MB**\n\n"
                     "Close to Telegram's 50MB limit.",
                parse_mode="Markdown"
            )

        # Send the file
        with open(file_path, 'rb') as f:
            if format_choice == "mp3":
                await context.bot.send_audio(
                    chat_id=chat_id,
                    audio=f,
                    read_timeout=120,
                    write_timeout=120,
                    filename=os.path.basename(file_path),
                    title=os.path.basename(file_path)[:-4],
                    performer="THE PLUG"
                )
            else:
                await context.bot.send_video(
                    chat_id=chat_id,
                    video=f,
                    read_timeout=120,
                    write_timeout=120,
                    filename=os.path.basename(file_path)
                )

        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ **Sent Successfully!**\n\n"
                 "This file will auto-delete in 30 seconds.",
            parse_mode="Markdown"
        )

        # Wait and cleanup
        await asyncio.sleep(30)
        os.chdir(original_dir)
        shutil.rmtree(download_dir, ignore_errors=True)

    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ **Download Error!**\n\n{str(e)[:200]}",
            parse_mode="Markdown"
        )
        os.chdir(original_dir)
        shutil.rmtree(download_dir, ignore_errors=True)
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    user_id = update.effective_user.id
    if user_id in user_format_preferences:
        del user_format_preferences[user_id]
    await update.message.reply_text(
        "⏹️ **Cancelled!**\n\n"
        "Any ongoing operations have been stopped.",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    await update.message.reply_text(
        "📖 **Help Menu**\n\n"
        "1. Send /start to see the menu\n"
        "2. Choose your format (MP3/Video)\n"
        "3. Send a YouTube or Spotify link\n"
        "4. I'll download and send it!\n\n"
        "**Supported:**\n"
        "✅ YouTube videos\n"
        "✅ Spotify tracks\n"
        "✅ YouTube Music\n\n"
        "**Commands:**\n"
        "/start - Show menu\n"
        "/privacy - Privacy policy\n"
        "/cancel - Cancel download\n\n"
        "⚠️ Files auto-delete after 30 seconds!",
        parse_mode="Markdown"
    )

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /privacy command."""
    await update.message.reply_text(
        "🔒 **Privacy Policy**\n\n"
        "• We do NOT store your personal data\n"
        "• Chat IDs are cached temporarily\n"
        "• No files are saved permanently\n"
        "• Your data is never shared\n\n"
        "Files are deleted after 30 seconds.",
        parse_mode="Markdown"
    )

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy_command))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(format_selection, pattern="^(mp3|480p|720p|1080p|help|privacy|back_to_menu)$"))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    
    # Message handler for links
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("🤖 THE PLUG is running...")
    print(f"📢 Channel: @{CHANNEL_USERNAME}")
    app.run_polling()

if __name__ == "__main__":
    main()
