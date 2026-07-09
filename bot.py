import logging
import subprocess
import os
import shutil
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# --- CONFIGURATION ---
BOT_TOKEN = "7869986791:AAERF18jdtPm_kmdaGqKKA3Ce6W18CGgAy8"
CHANNEL_ID = -1001886812003

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- SUBSCRIPTION CHECK FUNCTION ---
async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if a user is a member of the channel."""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- DECORATOR TO CHECK SUBSCRIPTION ON EVERY COMMAND ---
def require_subscription(func):
    """Decorator to check if user is subscribed before running command."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is subscribed
        if not await is_user_subscribed(context, user_id):
            keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/habitsofmusic")],
                        [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_sub")]]
            await update.message.reply_text(
                "🚫 **Access Denied!**\n\n"
                "You must be a member of @habitsofmusic to use this bot.\n\n"
                "👉 Click below to join, then verify!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        
        # User is subscribed, run the actual command
        return await func(update, context, *args, **kwargs)
    return wrapper

# --- DOWNLOAD FUNCTION ---
async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE, query: str):
    """Download and send audio using yt-dlp."""
    status_msg = await update.message.reply_text("🔍 Searching for your track... This may take a moment.")
    
    # Check if it's a YouTube link or search query
    is_youtube = 'youtube.com' in query or 'youtu.be' in query or 'spotify.com' in query
    
    download_dir = f"./downloads/{update.effective_user.id}"
    os.makedirs(download_dir, exist_ok=True)
    
    try:
        if is_youtube:
            # Use yt-dlp for YouTube/Spotify
            import yt_dlp
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=True)
                filename = ydl.prepare_filename(info)
                # Change extension from whatever to mp3
                mp3_file = filename.rsplit('.', 1)[0] + '.mp3'
                
                with open(mp3_file, 'rb') as audio:
                    await update.message.reply_audio(
                        audio=audio,
                        filename=os.path.basename(mp3_file),
                        caption=f"🎵 {info.get('title', 'Track')}"
                    )
                
                os.remove(mp3_file)
        else:
            # Use spotdl for search queries
            import spotdl
            # This needs the full implementation
            await status_msg.edit_text("❌ Search feature coming soon! Please send a YouTube or Spotify link.")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error: {str(e)[:200]}")
    finally:
        shutil.rmtree(download_dir, ignore_errors=True)
        await status_msg.delete()
# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_user_subscribed(context, user_id):
        keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/habitsofmusic")],
                    [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_sub")]]
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\n"
            "You must join @habitsofmusic to use this bot.\n\n"
            "Click below to join, then verify!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(
        "✅ **Welcome to THE PLUG!**\n\n"
        "🎵 I can download music from Spotify and YouTube!\n\n"
        "**How to use:**\n"
        "• Send me a Spotify or YouTube **LINK**\n"
        "• Or use /track to search for a song\n"
        "• Use /album to search for an album\n\n"
        "**Commands:**\n"
        "/start - Start the bot\n"
        "/track - Search for a track\n"
        "/album - Search for an album\n"
        "/help - Show all commands\n"
        "/privacy - Privacy policy\n"
        "/cancel - Cancel current operation\n\n"
        "⚠️ *You must watch an ad before downloading!*"
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for the 'Check Again' button."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if await is_user_subscribed(context, user_id):
        await query.edit_message_text(
            "✅ **Subscription Verified!**\n\n"
            "You now have full access to the bot!\n"
            "Send /start to see all commands."
        )
    else:
        await query.answer("❌ You haven't joined yet! Please join and try again.", show_alert=True)

@require_subscription
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎵 **Track Search**\n\n"
        "Please send me the song name or Spotify/YouTube link.\n\n"
        "Example: `Shape of You` or `https://open.spotify.com/track/...`"
    )
    # Store that user is in track mode
    context.user_data['mode'] = 'track'

@require_subscription
async def album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💿 **Album Search**\n\n"
        "Please send me the album name or Spotify/YouTube link.\n\n"
        "Example: `Thriller` or `https://open.spotify.com/album/...`"
    )
    context.user_data['mode'] = 'album'

@require_subscription
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Help Menu**\n\n"
        "/start - Start the bot\n"
        "/track - Search for a track\n"
        "/album - Search for an album\n"
        "/privacy - Show privacy policy\n"
        "/cancel - Cancel current operation\n\n"
        "**Quick Tip:**\n"
        "Just paste a Spotify or YouTube link and I'll download it!\n\n"
        "⚠️ **Important:**\n"
        "• You must be a member of @habitsofmusic\n"
        "• You must watch an ad before downloading"
    )

@require_subscription
async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 **Privacy Policy**\n\n"
        "• We do not store your personal data\n"
        "• Chat IDs are cached temporarily for functionality\n"
        "• No music files are saved permanently on our servers\n"
        "• Your data is never shared with third parties"
    )

@require_subscription
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("⏹️ **Cancelled**\n\nAll ongoing operations have been stopped.")

# --- MESSAGE HANDLER FOR LINKS AND SEARCH QUERIES ---
@require_subscription
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user messages (links or search queries)."""
    text = update.message.text
    user_id = update.effective_user.id
    
    # Check if it's a Spotify or YouTube link
    spotify_pattern = r'(https?://)?(www\.)?(open\.spotify\.com|spotify\.com)/'
    youtube_pattern = r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
    
    if re.search(spotify_pattern, text) or re.search(youtube_pattern, text):
        # It's a link - download directly
        await download_and_send(update, context, text)
    else:
        # It's a search query - use spotdl to search
        mode = context.user_data.get('mode', 'track')
        await download_and_send(update, context, text)

# --- MAIN FUNCTION ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("album", album))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Add callback handler for the "Check Again" button
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    
    # Add message handler for links and text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))
    
    print("🤖 THE PLUG is running...")
    print(f"📢 Checking subscription for channel ID: {CHANNEL_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# --- SUBSCRIPTION CHECK FUNCTION ---
async def is_user_subscribed(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    """Check if a user is a member of the channel."""
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# --- DECORATOR TO CHECK SUBSCRIPTION ON EVERY COMMAND ---
def require_subscription(func):
    """Decorator to check if user is subscribed before running command."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is subscribed
        if not await is_user_subscribed(context, user_id):
            keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/habitsofmusic")],
                        [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_sub")]]
            await update.message.reply_text(
                "🚫 **Access Denied!**\n\n"
                "You must be a member of @habitsofmusic to use this bot.\n\n"
                "👉 Click below to join, then verify!",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return
        
        # User is subscribed, run the actual command
        return await func(update, context, *args, **kwargs)
    return wrapper

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not await is_user_subscribed(context, user_id):
        keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/habitsofmusic")],
                    [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_sub")]]
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\n"
            "You must join @habitsofmusic to use this bot.\n\n"
            "Click below to join, then verify!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(
        "✅ **Welcome to THE PLUG!**\n\n"
        "🎵 I can download music from Spotify and YouTube!\n\n"
        "**Commands:**\n"
        "/track - Search for a track\n"
        "/album - Search for an album\n"
        "/help - Show all commands\n"
        "/privacy - Privacy policy\n"
        "/cancel - Cancel current operation\n\n"
        "⚠️ *Note:* You must watch an ad before downloading!"
    )

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback for the 'Check Again' button."""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if await is_user_subscribed(context, user_id):
        await query.edit_message_text(
            "✅ **Subscription Verified!**\n\n"
            "You now have full access to the bot!\n"
            "Send /start to see all commands."
        )
    else:
        await query.answer("❌ You haven't joined yet! Please join and try again.", show_alert=True)

@require_subscription
async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 **Track Search**\n\nPlease send me the song name you want to download.\n\n*Note: You must watch an ad before downloading!*")

@require_subscription
async def album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💿 **Album Search**\n\nPlease send me the album name you want to download.\n\n*Note: You must watch an ad before downloading!*")

@require_subscription
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 **Help Menu**\n\n"
        "/start - Start the bot\n"
        "/track - Search for a track\n"
        "/album - Search for an album\n"
        "/privacy - Show privacy policy\n"
        "/cancel - Cancel current operation\n\n"
        "⚠️ **Important:**\n"
        "• You must be a member of @habitsofmusic\n"
        "• You must watch an ad before downloading"
    )

@require_subscription
async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🔒 **Privacy Policy**\n\n"
        "• We do not store your personal data\n"
        "• Chat IDs are cached temporarily for functionality\n"
        "• No music files are saved permanently on our servers\n"
        "• Your data is never shared with third parties"
    )

@require_subscription
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("⏹️ **Cancelled**\n\nAll ongoing operations have been stopped.")

# --- MAIN FUNCTION ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("album", album))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("cancel", cancel))
    
    # Add callback handler for the "Check Again" button
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    
    print("🤖 THE PLUG is running...")
    print(f"📢 Checking subscription for channel ID: {CHANNEL_ID}")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
