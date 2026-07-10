'''
THE PLUG - MP3 Downloader Bot
✅ Downloads from Deezer (best quality, no blocking)
✅ Falls back to YouTube/Spotify if Deezer fails
✅ Channel subscription required
✅ Users KEEP their downloaded files
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
CHANNEL_USERNAME = "habitsofmusic"
CHANNEL_LINK = "https://t.me/habitsofmusic"
SUPPORT_AD_LINK = "https://your-ad-link.com"

# --- DEEZER ARL COOKIE ---
DEEZER_ARL = "5fa1931347e4baec15cd38eff6de9f0f47bd764ce7d06ca62ca9af37e5acc6bf36db17ce66ffa00fa29fc200de3e91ef8181eabd6c1b246a00483ec93cdc750e8119f6eacaf960543b8ef7d7ac70c77fe903364a6d1701495a97a99d8cc33b8e"

# --- SUBSCRIPTION CHECK ---
async def check_user_joined_channel(app, user_id):
    try:
        member = await app.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"[Channel Join Check Error] {e}")
        return False

# --- DEEZER DOWNLOAD FUNCTION ---
async def download_from_deezer(chat_id, context, url):
    """Download MP3 from Deezer using the ARL cookie."""
    try:
        # Try to import deezloader or deezspot
        try:
            from deezspot.deezloader import DeeLogin
            deezer = DeeLogin(arl=DEEZER_ARL)
        except ImportError:
            # Fallback: use subprocess with deezloader
            download_dir = f"./downloads/{chat_id}"
            os.makedirs(download_dir, exist_ok=True)
            
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
            
            # Find downloaded file
            files = glob.glob(f"{download_dir}/*.mp3")
            if files:
                return files[0], None
            return None, "No MP3 file created"
        
        # If using deezspot library directly
        download_dir = f"./downloads/{chat_id}"
        os.makedirs(download_dir, exist_ok=True)
        
        deezer.download_trackdee(
            link_track=url,
            output_dir=download_dir,
            quality_download='MP3_320'
        )
        
        # Find downloaded file
        files = glob.glob(f"{download_dir}/*.mp3")
        if files:
            return files[0], None
        return None, "No MP3 file created"
        
    except Exception as e:
        return None, str(e)

# --- YOUTUBE DOWNLOAD FUNCTION ---
async def download_from_youtube(chat_id, url):
    """Download MP3 from YouTube."""
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

# --- SPOTIFY SEARCH FUNCTION ---
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
            return None, stderr.decode().strip()
        
        files = glob.glob(f"{download_dir}/*.mp3")
        if files:
            return files[0], None
        return None, "No MP3 file created"
        
    except Exception as e:
        return None, str(e)

# --- COMMAND HANDLERS ---

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
        "I can download MP3 from Deezer, YouTube, and Spotify!\n\n"
        "How to use:\n"
        "1️⃣ Choose a source below\n"
        "2️⃣ Send me a link\n"
        "3️⃣ I'll download the MP3 and send it!\n\n"
        "🔹 Deezer is best - no blocking!",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🎵 Deezer", callback_data="deezer"),
                InlineKeyboardButton("🎵 YouTube", callback_data="youtube"),
                InlineKeyboardButton("🎵 Spotify", callback_data="spotify")
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
    query = update.callback_query
    user_id = query.from_user.id
    choice = query.data
    await query.answer()
    
    if choice == "help":
        await query.edit_message_text(
            "📖 Help Menu\n\n"
            "1. Choose Deezer, YouTube, or Spotify\n"
            "2. Send me a link\n"
            "3. I'll download the MP3 and send it!\n\n"
            "Commands:\n"
            "/start - Show this menu\n"
            "/privacy - Privacy policy\n"
            "/cancel - Cancel download\n\n"
            "Supported:\n"
            "✅ Deezer tracks\n"
            "✅ YouTube videos\n"
            "✅ Spotify tracks\n\n"
            "💾 Your downloaded files are yours to keep!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    if choice == "privacy":
        await query.edit_message_text(
            "🔒 Privacy Policy\n\n"
            "• We do NOT store your personal data\n"
            "• Chat IDs are cached temporarily\n"
            "• No files are saved permanently on our servers\n"
            "• Your data is never shared\n\n"
            "💾 Files are sent directly to you and not stored.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data="back_to_menu")]
            ])
        )
        return
    
    if choice == "back_to_menu":
        await query.edit_message_text(
            "🎵 Welcome to THE PLUG!\n\nChoose your source:",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("🎵 Deezer", callback_data="deezer"),
                    InlineKeyboardButton("🎵 YouTube", callback_data="youtube"),
                    InlineKeyboardButton("🎵 Spotify", callback_data="spotify")
                ],
                [
                    InlineKeyboardButton("❓ Help", callback_data="help"),
                    InlineKeyboardButton("🔒 Privacy", callback_data="privacy")
                ]
            ])
        )
        return
    
    # Store the user's choice
    context.user_data['source'] = choice
    source_name = "Deezer" if choice == "deezer" else ("YouTube" if choice == "youtube" else "Spotify")
    
    await query.edit_message_text(
        f"✅ Source selected: {source_name}\n\n"
        f"Now send me a link!\n\n"
        f"Example: { 'https://www.deezer.com/track/...' if choice == 'deezer' else ('https://www.youtube.com/watch?v=...' if choice == 'youtube' else 'https://open.spotify.com/track/...') }\n\n"
        "💾 Your file is yours to keep!"
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
            "Send /start to see the menu."
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

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
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

    # Get source preference (default to deezer)
    source = context.user_data.get('source', 'deezer')
    
    await update.message.reply_text(
        f"✅ Received!\n\nSource: {source.capitalize()}\n"
        "⏳ Downloading MP3, please wait..."
    )
    
    # Start download
    asyncio.create_task(handle_download_and_send(chat_id, url, context, source))

async def handle_download_and_send(chat_id, url, context, source):
    file_path = None
    error = None
    
    try:
        # Try Deezer first if source is deezer or auto
        if source == "deezer" or source == "auto":
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎵 Downloading from Deezer..."
            )
            file_path, error = await download_from_deezer(chat_id, context, url)
            
            if file_path:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="✅ Downloaded from Deezer!"
                )
        
        # If Deezer failed or not selected, try YouTube
        if not file_path and (source == "youtube" or source == "auto"):
            if source == "auto" and error and "Deezer" in error:
                await context.bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ Deezer failed, trying YouTube..."
                )
            
            if "youtube.com" in url or "youtu.be" in url:
                file_path, error = await download_from_youtube(chat_id, url)
            elif "spotify.com" in url:
                file_path, error = await search_spotify_and_download(chat_id, url)
            else:
                # Try to detect link type
                if "deezer.com" in url:
                    file_path, error = await download_from_deezer(chat_id, context, url)
                else:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text="❌ Unsupported link format!\n\nPlease send a valid Deezer, YouTube, or Spotify link."
                    )
                    return
        
        # If still no file, try Spotify fallback
        if not file_path and "spotify.com" in url:
            await context.bot.send_message(
                chat_id=chat_id,
                text="🎵 Searching Spotify on YouTube..."
            )
            file_path, error = await search_spotify_and_download(chat_id, url)
        
        # Check if we have a file
        if not file_path:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Download Failed!\n\nError: {error or 'Unknown error'}"
            )
            return
        
        # Check file size
        file_size = os.path.getsize(file_path) / (1024 * 1024)
        if file_size > 48:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⚠️ File is {file_size:.1f}MB\n\nClose to Telegram's 50MB limit."
            )
        
        # Send the MP3
        with open(file_path, 'rb') as f:
            await context.bot.send_audio(
                chat_id=chat_id,
                audio=f,
                read_timeout=120,
                write_timeout=120,
                filename=os.path.basename(file_path),
                title=os.path.basename(file_path)[:-4],
                performer="THE PLUG"
            )
        
        await context.bot.send_message(
            chat_id=chat_id,
            text="✅ **Sent Successfully!**\n\n"
                 "💾 This file is yours to keep!\n\n"
                 "To download more, just send another link.\n"
                 "Send /start to go back to the menu."
        )
        
        # Clean up
        try:
            os.remove(file_path)
        except:
            pass
            
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"❌ Download Error!\n\n{str(e)[:200]}"
        )
    finally:
        # Clean up download directory
        try:
            download_dir = f"./downloads/{chat_id}"
            shutil.rmtree(download_dir, ignore_errors=True)
        except:
            pass

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data.clear()
    await update.message.reply_text(
        "⏹️ Cancelled!\n\nAny ongoing operations have been stopped."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Help Menu\n\n"
        "1. Send /start to see the menu\n"
        "2. Choose Deezer, YouTube, or Spotify\n"
        "3. Send me a link\n"
        "4. I'll download the MP3 and send it!\n\n"
        "Supported:\n"
        "✅ Deezer tracks (BEST - no blocking)\n"
        "✅ YouTube videos\n"
        "✅ Spotify tracks\n\n"
        "Commands:\n"
        "/start - Show menu\n"
        "/privacy - Privacy policy\n"
        "/cancel - Cancel download\n\n"
        "💾 Your downloaded files are yours to keep!"
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

# --- MAIN ---
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy_command))
    app.add_handler(CommandHandler("cancel", cancel))
    
    app.add_handler(CallbackQueryHandler(format_selection, pattern="^(deezer|youtube|spotify|help|privacy|back_to_menu)$"))
    app.add_handler(CallbackQueryHandler(check_join_callback, pattern="^check_join$"))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    
    print("🤖 THE PLUG is running...")
    print(f"📢 Channel: @{CHANNEL_USERNAME}")
    print("🎵 Sources: Deezer (ARL loaded), YouTube, Spotify")
    app.run_polling()

if __name__ == "__main__":
    main()
