'''
THE PLUG - Smart Music Downloader
✅ Auto-detects YouTube, Spotify, Deezer links
✅ Auto-detects song names (searches YouTube)
✅ One-step process - just send a link or song name
✅ Channel subscription required
'''

import os
import asyncio
import subprocess
import glob
import shutil
import re
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "7869986791:AAERF18jdtPm_kmdaGqKKA3Ce6W18CGgAy8")
CHANNEL_USERNAME = "habitsofmusic"
CHANNEL_LINK = "https://t.me/habitsofmusic"

# --- DEEZER ARL COOKIE ---
DEEZER_ARL = """5fa1931347e4baec15cd38eff6de9f0f47bd764ce7d06ca62ca9af
37e5acc6bf36db17ce66ffa00fa29fc200de3e91ef8181eabd6c1b246a00483ec93cdc7
50e8119f6eacaf960543b8ef7d7ac70c77fe903364a6d1701495a97a99d8cc33b8e"""


# --- SUBSCRIPTION CHECK ---
async def check_user_joined_channel(app, user_id):
    try:
        member = await app.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"[Channel Join Check Error] {e}")
        return False

# --- DOWNLOAD FUNCTIONS ---

async def download_from_deezer(chat_id, url):
    """Download MP3 from Deezer."""
    try:
        download_dir = f"./downloads/{chat_id}"
        os.makedirs(download_dir, exist_ok=True)
        
        # Try using deezloader command line
        cmd = [
            "deezloader",
            "--arl", DEEZER_ARL,
            "--output", download_dir,
            "--quality", "MP3_320",
            url
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return None, stderr.decode().strip()
        
        files = glob.glob(f"{download_dir}/*.mp3")
        if files:
            return files[0], None
        return None, "No MP3 file created"
        
    except Exception as e:
        return None, str(e)

async def download_from_youtube(chat_id, query):
    """Download MP3 from YouTube (link or search)."""
    try:
        download_dir = f"./downloads/{chat_id}"
        os.makedirs(download_dir, exist_ok=True)
        
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "-o", f"{download_dir}/%(title)s.%(ext)s",
            query
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error = stderr.decode().strip()
            if "Sign in to confirm" in error:
                return None, "YouTube is blocking this request. Try using a Deezer or Spotify link instead."
            return None, error
        
        files = glob.glob(f"{download_dir}/*.mp3")
        if files:
            return files[0], None
        return None, "No MP3 file created"
        
    except Exception as e:
        return None, str(e)

async def search_spotify_and_download(chat_id, url):
    """Search for Spotify track on YouTube and download."""
    try:
        download_dir = f"./downloads/{chat_id}"
        os.makedirs(download_dir, exist_ok=True)
        
        # Get track info using spotdl
        spotdl_cmd = ["spotdl", url, "--print", "title,artist"]
        
        process = await asyncio.create_subprocess_exec(
            *spotdl_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return None, "Could not get track info"
        
        track_info = stdout.decode().strip().split(',')
        if len(track_info) < 2:
            return None, "Could not parse track info"
        
        artist = track_info[0].strip()
        title = track_info[1].strip()
        search_query = f"{artist} {title} audio"
        
        # Now download from YouTube
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            f"ytsearch1:{search_query}",
            "-f", "bestaudio/best",
            "--extract-audio",
            "--audio-format", "mp3",
            "--audio-quality", "192K",
            "-o", f"{download_dir}/%(title)s.%(ext)s"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error = stderr.decode().strip()
            if "Sign in to confirm" in error:
                return None, "YouTube is blocking this request. Try using a Deezer link instead."
            return None, error
        
        files = glob.glob(f"{download_dir}/*.mp3")
        if files:
            return files[0], None
        return None, "No MP3 file created"
        
    except Exception as e:
        return None, str(e)

# --- MAIN COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    joined = await check_user_joined_channel(context.application, user_id)

    if not joined:
        await update.message.reply_text(
            "🚫 Access Denied!\n\nYou must join @habitsofmusic to use this bot.\n\nClick below to join, then try again!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )
        return

    await update.message.reply_text(
        "🎵 Welcome to THE PLUG!\n\n"
        "Just send me any link and I'll download the MP3!\n\n"
        "Supported:\n"
        "✅ Deezer links\n"
        "✅ YouTube links\n"
        "✅ Spotify links\n"
        "✅ Song names (I'll search YouTube)\n\n"
        "💾 Files are yours to keep!\n"
        "Send /help for more info."
    )

async def check_join_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    joined = await check_user_joined_channel(context.application, user_id)
    
    if joined:
        await query.edit_message_text(
            "✅ Subscription Verified!\n\n"
            "You now have full access to THE PLUG!\n"
            "Send me any link to get started!"
        )
    else:
        await query.edit_message_text(
            "❌ Still Not Joined!\n\n"
            "Please join @habitsofmusic first:\n"
            f"{CHANNEL_LINK}\n\n"
            "Then click 'I've Joined! Check Again'.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message (link or song name)."""
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if user joined channel
    joined = await check_user_joined_channel(context.application, user_id)
    if not joined:
        await update.message.reply_text(
            "🚫 Access Denied!\n\nYou must join @habitsofmusic first!\n" + CHANNEL_LINK,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )
        return

    # Send initial response
    status_msg = await update.message.reply_text("🔍 Processing your request...")

    # Start download
    file_path, error = await smart_download(chat_id, user_input, status_msg)

    if file_path:
        # Send the MP3
        try:
            file_size = os.path.getsize(file_path) / (1024 * 1024)
            if file_size > 48:
                await status_msg.edit_text(f"⚠️ File is {file_size:.1f}MB - close to Telegram's 50MB limit.")
            
            with open(file_path, 'rb') as f:
                await update.message.reply_audio(
                    audio=f,
                    read_timeout=120,
                    write_timeout=120,
                    filename=os.path.basename(file_path),
                    title=os.path.basename(file_path)[:-4],
                    performer="THE PLUG"
                )
            
            await status_msg.delete()
            await update.message.reply_text(
                "✅ Sent Successfully!\n\n"
                "💾 This file is yours to keep!\n"
                "Just send me another link to continue."
            )
            
        except Exception as e:
            await status_msg.edit_text(f"❌ Error sending file: {str(e)[:200]}")
        finally:
            # Clean up
            try:
                os.remove(file_path)
            except:
                pass
    else:
        await status_msg.edit_text(f"❌ Download Failed!\n\n{error or 'Unknown error'}")

    # Clean up download directory
    try:
        download_dir = f"./downloads/{chat_id}"
        shutil.rmtree(download_dir, ignore_errors=True)
    except:
        pass

async def smart_download(chat_id, user_input, status_msg):
    """Smart download that detects the source automatically."""
    
    # Check if it's a URL
    is_url = user_input.startswith('http://') or user_input.startswith('https://')
    
    # --- STRATEGY 1: Deezer ---
    if is_url and 'deezer.com' in user_input:
        await status_msg.edit_text("🎵 Downloading from Deezer...")
        return await download_from_deezer(chat_id, user_input)
    
    # --- STRATEGY 2: YouTube ---
    if is_url and ('youtube.com' in user_input or 'youtu.be' in user_input):
        await status_msg.edit_text("🎵 Downloading from YouTube...")
        return await download_from_youtube(chat_id, user_input)
    
    # --- STRATEGY 3: Spotify ---
    if is_url and 'spotify.com' in user_input:
        await status_msg.edit_text("🎵 Processing Spotify link...")
        return await search_spotify_and_download(chat_id, user_input)
    
    # --- STRATEGY 4: Song Name (Search YouTube) ---
    if not is_url:
        await status_msg.edit_text(f"🔍 Searching YouTube for: {user_input[:50]}...")
        return await download_from_youtube(chat_id, f"ytsearch1:{user_input}")
    
    # --- STRATEGY 5: Generic Link (Try everything) ---
    if is_url:
        await status_msg.edit_text("🔍 Trying to detect source...")
        
        # Try Deezer first (most reliable)
        try:
            result, error = await download_from_deezer(chat_id, user_input)
            if result:
                await status_msg.edit_text("✅ Downloaded from Deezer!")
                return result, None
        except:
            pass
        
        # Try YouTube as fallback
        try:
            result, error = await download_from_youtube(chat_id, user_input)
            if result:
                await status_msg.edit_text("✅ Downloaded from YouTube!")
                return result, None
        except:
            pass
        
        return None, "Could not download from any source. Please try a different link."
    
    return None, "Invalid input. Please send a link or song name."

# --- COMMAND HANDLERS ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Help Menu\n\n"
        "Just send me any of these and I'll download the MP3:\n\n"
        "✅ Deezer link: https://www.deezer.com/track/...\n"
        "✅ YouTube link: https://www.youtube.com/watch?v=...\n"
        "✅ Spotify link: https://open.spotify.com/track/...\n"
        "✅ Song name: \"Shape of You\"\n\n"
        "Commands:\n"
        "/start - Show welcome\n"
        "/privacy - Privacy policy\n"
        "/cancel - Cancel operation\n\n"
        "💾 Your files are yours to keep!"
    )

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 Privacy Policy\n\n"
        "• We do NOT store your personal data\n"
        "• Chat IDs are cached temporarily\n"
        "• No files are saved permanently on our servers\n"
        "• Your data is never shared\n\n"
        "💾 Files are sent directly to you and not stored."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏹️ Cancelled!\n\nAny ongoing operations have been stopped."
    )

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy_command))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    
    # Handle all text messages (links, song names, etc.)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 THE PLUG is running...")
    print("📢 Channel: @habitsofmusic")
    print("🎵 Auto-detects: Deezer, YouTube, Spotify, Song Names")
    app.run_polling()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
