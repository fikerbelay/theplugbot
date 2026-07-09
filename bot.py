import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

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
