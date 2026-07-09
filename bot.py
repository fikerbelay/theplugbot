import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIGURATION ---
BOT_TOKEN = "7869986791:AAERF18jdtPm_kmdaGqKKA3Ce6W18CGgAy8" 
CHANNEL_ID = -1001886812003

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_member = member.status in ["member", "administrator", "creator"]
    except:
        is_member = False
    
    if not is_member:
        keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/habitsofmusic")],
                    [InlineKeyboardButton("✅ I've Joined!", callback_data="check_sub")]]
        await update.message.reply_text(
            "🚫 **Access Denied!**\n\nYou must join @habitsofmusic to use this bot.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text("✅ **Welcome to THE PLUG!**\n\nCommands:\n/track - Search track\n/album - Search album\n/help - Help\n/privacy - Privacy\n/cancel - Cancel")

async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        is_member = member.status in ["member", "administrator", "creator"]
    except:
        is_member = False
    
    if is_member:
        await query.edit_message_text("✅ Verified! You now have full access!")
    else:
        await query.answer("❌ Not joined yet!", show_alert=True)

async def track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎵 Track search coming soon!")

async def album(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💿 Album search coming soon!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("/start - Start\n/track - Track\n/album - Album\n/privacy - Privacy\n/cancel - Cancel")

async def privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔒 No data stored.")

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("⏹️ Cancelled.")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("track", track))
    app.add_handler(CommandHandler("album", album))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("privacy", privacy))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(check_subscription, pattern="check_sub"))
    
    print("🤖 THE PLUG is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
