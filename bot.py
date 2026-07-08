import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIGURATION ---
# YOU MUST CHANGE THESE TWO THINGS:
BOT_TOKEN = "YOUR_NEW_TOKEN_HERE"  # Get from @BotFather after revoking
CHANNEL_USERNAME = "@habitsofmusic"
CHANNEL_ID = -1001234567890  # We'll find this number later

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

async def is_user_subscribed(context, user_id):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def start(update, context):
    user_id = update.effective_user.id
    if not await is_user_subscribed(context, user_id):
        keyboard = [[InlineKeyboardButton("📢 JOIN CHANNEL", url="https://t.me/habitsofmusic")],
                    [InlineKeyboardButton("✅ I've Joined! Check Again", callback_data="check_sub")]]
        await update.message.reply_text(
            f"🚫 **Access Denied!**\n\nYou must join @habitsofmusic to use this bot.\n"
            f"Click below to join, then verify!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return
    
    await update.message.reply_text(
        f"✅ **Welcome to THE PLUG!**\n\n"
        f"Commands:\n"
        f"/track - Search track\n"
        f"/album - Search album\n"
        f"/help - All commands\n"
        f"/privacy - Privacy policy\n"
        f"/cancel - Cancel operation\n\n"
        f"⚠️ Watch an ad before downloading!"
    )

async def check_subscription(update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if await is_user_subscribed(context, user_id):
        await query.edit_message_text("✅ Verified! You now have full access. Use /start")
    else:
        await query.answer("❌ Not joined yet! Join and try again.", show_alert=True)

async def track(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await update.message.reply_text("❌ Join @habitsofmusic first! Use /start")
        return
    await update.message.reply_text("🎵 Track search coming soon!")

async def album(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await update.message.reply_text("❌ Join @habitsofmusic first! Use /start")
        return
    await update.message.reply_text("💿 Album search coming soon!")

async def help_command(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await update.message.reply_text("❌ Join @habitsofmusic first! Use /start")
        return
    await update.message.reply_text("/start - Start\n/track - Track\n/album - Album\n/privacy - Privacy\n/cancel - Cancel")

async def privacy(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await update.message.reply_text("❌ Join @habitsofmusic first! Use /start")
        return
    await update.message.reply_text("🔒 No data stored. Chat IDs cached temporarily.")

async def cancel(update, context):
    if not await is_user_subscribed(context, update.effective_user.id):
        await update.message.reply_text("❌ Join @habitsofmusic first! Use /start")
        return
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