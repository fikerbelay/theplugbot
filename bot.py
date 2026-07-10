'''
THE PLUG - Smart Music Downloader with Selection
✅ Extracts artist/title from Deezer, Spotify, YouTube links
✅ Searches YouTube and shows options
✅ User selects which version to download
✅ Channel subscription required
'''

import os
import asyncio
import subprocess
import glob
import shutil
import re
import json
from urllib.parse import urlparse
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "7869986791:AAERF18jdtPm_kmdaGqKKA3Ce6W18CGgAy8")
CHANNEL_USERNAME = "habitsofmusic"
CHANNEL_LINK = "https://t.me/habitsofmusic"

# --- SUBSCRIPTION CHECK ---
async def check_user_joined_channel(app, user_id):
    try:
        member = await app.bot.get_chat_member(chat_id=f"@{CHANNEL_USERNAME}", user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception as e:
        print(f"[Channel Join Check Error] {e}")
        return False

# --- EXTRACT SONG INFO FROM LINKS ---

async def extract_from_spotify(url):
    """Extract artist and title from Spotify link."""
    try:
        cmd = ["spotdl", url, "--print", "title,artist"]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(timeout=30)
        
        if process.returncode == 0 and stdout:
            parts = stdout.decode().strip().split(',')
            if len(parts) >= 2:
                return parts[0].strip(), parts[1].strip()
        return None, None
    except:
        return None, None

async def extract_from_deezer(url):
    """Extract artist and title from Deezer link."""
    try:
        # Use deezloader to get info
        cmd = ["deezloader", "--arl", DEEZER_ARL, "--info", url]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(timeout=30)
        
        if process.returncode == 0 and stdout:
            # Parse the output (simplified)
            output = stdout.decode().strip()
            # Try to extract title and artist
            title_match = re.search(r'Title:\s*(.+?)(?:\n|$)', output)
            artist_match = re.search(r'Artist:\s*(.+?)(?:\n|$)', output)
            
            if title_match and artist_match:
                return title_match.group(1).strip(), artist_match.group(1).strip()
        return None, None
    except:
        return None, None

async def extract_from_youtube(url):
    """Extract video title from YouTube link."""
    try:
        cmd = ["yt-dlp", "--get-title", url]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(timeout=30)
        
        if process.returncode == 0 and stdout:
            title = stdout.decode().strip()
            # Try to parse "Artist - Title" format
            if ' - ' in title:
                parts = title.split(' - ', 1)
                return parts[1], parts[0]  # title, artist
            return title, None
        return None, None
    except:
        return None, None

async def extract_song_info(url):
    """Extract artist and title from any music link."""
    if 'spotify.com' in url:
        return await extract_from_spotify(url)
    elif 'deezer.com' in url:
        return await extract_from_deezer(url)
    elif 'youtube.com' in url or 'youtu.be' in url:
        return await extract_from_youtube(url)
    else:
        # Assume it's a song name input
        return url, None

# --- SEARCH YOUTUBE FOR SONGS ---

async def search_youtube(query):
    """Search YouTube for a song and return results."""
    try:
        cmd = [
            "yt-dlp",
            "--js-runtimes", "node",
            "--flat-playlist",
            "--dump-json",
            f"ytsearch10:{query}"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate(timeout=60)
        
        if process.returncode != 0:
            return []
        
        results = []
        # Parse JSON lines
        for line in stdout.decode().strip().split('\n'):
            if line:
                try:
                    data = json.loads(line)
                    results.append({
                        'title': data.get('title', 'Unknown'),
                        'id': data.get('id', ''),
                        'url': f"https://www.youtube.com/watch?v={data.get('id', '')}",
                        'duration': data.get('duration', 0),
                        'uploader': data.get('uploader', 'Unknown')
                    })
                except:
                    continue
        
        return results
    
    except Exception as e:
        print(f"Search error: {e}")
        return []

# --- DOWNLOAD FROM YOUTUBE ---

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
        stdout, stderr = await process.communicate(timeout=180)
        
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
            "🚫 Access Denied!\n\nYou must join @habitsofmusic to use this bot.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )
        return

    await update.message.reply_text(
        "🎵 Welcome to THE PLUG!\n\n"
        "Send me any link or song name and I'll:\n"
        "1️⃣ Find the song info\n"
        "2️⃣ Search YouTube for matches\n"
        "3️⃣ Show you options\n"
        "4️⃣ Download the one you pick!\n\n"
        "Supported:\n"
        "✅ Deezer links\n"
        "✅ Spotify links\n"
        "✅ YouTube links\n"
        "✅ Song names\n\n"
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
            "Please join @habitsofmusic first:",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )

# --- HANDLE MESSAGES ---

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any message (link or song name)."""
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    # Check if user joined channel
    joined = await check_user_joined_channel(context.application, user_id)
    if not joined:
        await update.message.reply_text(
            "🚫 Access Denied!\n\nYou must join @habitsofmusic first!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_join")]
            ])
        )
        return

    # Send initial response
    status_msg = await update.message.reply_text("🔍 Processing your request...")

    # Extract song info
    title, artist = await extract_song_info(user_input)
    
    if not title and not artist:
        await status_msg.edit_text(
            "❌ Could not find song info.\n\n"
            "Please send a valid link or song name."
        )
        return

    # Build search query
    if artist and title:
        search_query = f"{artist} {title}"
        display_name = f"{artist} - {title}"
    elif title:
        search_query = title
        display_name = title
    else:
        await status_msg.edit_text("❌ Could not identify the song.")
        return

    await status_msg.edit_text(f"🔍 Searching YouTube for: {display_name}...")

    # Search YouTube
    results = await search_youtube(search_query)
    
    if not results:
        await status_msg.edit_text(
            f"❌ No results found for: {display_name}\n\n"
            "Please try a different search term."
        )
        return

    # Store results in context for callback
    context.user_data['search_results'] = results
    context.user_data['chat_id'] = chat_id

    # Show options to user
    keyboard = []
    for i, result in enumerate(results[:10]):  # Max 10 results
        duration = result.get('duration', 0)
        duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "Unknown"
        button_text = f"{i+1}. {result['title'][:40]} ({duration_str})"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_{i}")])

    keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_select")])

    await status_msg.edit_text(
        f"🔍 Found {len(results)} results for: {display_name}\n\n"
        "Select the one you want to download:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# --- HANDLE SELECTION ---

async def selection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_select":
        await query.edit_message_text("❌ Search cancelled.")
        return
    
    if not data.startswith("select_"):
        return
    
    # Get selection index
    try:
        index = int(data.split("_")[1])
    except:
        await query.edit_message_text("❌ Invalid selection.")
        return
    
    # Get results from context
    results = context.user_data.get('search_results', [])
    chat_id = context.user_data.get('chat_id')
    
    if not results or index >= len(results):
        await query.edit_message_text("❌ Selection expired. Please search again.")
        return
    
    selected = results[index]
    
    await query.edit_message_text(
        f"🎵 Downloading: {selected['title'][:60]}...\n\n"
        f"⏳ This may take a moment."
    )
    
    # Download the selected video
    file_path, error = await download_from_youtube(chat_id, selected['url'])
    
    if file_path:
        try:
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
                text="✅ Sent Successfully!\n\n"
                     "💾 This file is yours to keep!\n"
                     "Just send me another link to continue."
            )
            
            # Clean up
            os.remove(file_path)
            
            # Delete the selection message
            await query.message.delete()
            
        except Exception as e:
            await query.edit_message_text(f"❌ Error sending file: {str(e)[:200]}")
    else:
        await query.edit_message_text(
            f"❌ Download Failed!\n\n{error or 'Unknown error'}"
        )
    
    # Clean up search results
    context.user_data.pop('search_results', None)
    context.user_data.pop('chat_id', None)

    # Clean up download directory
    try:
        download_dir = f"./downloads/{chat_id}"
        shutil.rmtree(download_dir, ignore_errors=True)
    except:
        pass

# --- COMMAND HANDLERS ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 Help Menu\n\n"
        "Send me any of these and I'll find it:\n\n"
        "✅ Deezer link: https://www.deezer.com/track/...\n"
        "✅ Spotify link: https://open.spotify.com/track/...\n"
        "✅ YouTube link: https://www.youtube.com/watch?v=...\n"
        "✅ Song name: \"Shape of You\"\n\n"
        "I'll search YouTube and show you options to choose from!\n\n"
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
        "• No files are saved permanently\n"
        "• Your data is never shared\n\n"
        "💾 Files are sent directly to you and not stored."
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
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
    app.add_handler(CallbackQueryHandler(selection_callback, pattern="^(select_|cancel_select)"))
    
    # Handle all text messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 THE PLUG is running...")
    print("📢 Channel: @habitsofmusic")
    print("🎵 Smart Search + Selection Mode")
    app.run_polling()

if __name__ == "__main__":
    main()
