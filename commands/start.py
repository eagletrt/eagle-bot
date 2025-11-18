import logging
from telegram import Update
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting and logs who started the bot."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/start - User without username attempted to use /start command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return

    logging.info(f"commands/start - User @{username} started the bot")
    await update.message.reply_sticker(
        sticker="CAACAgQAAxkBAAE94hJpGMjqZi9VR1ee2gbzFw7POwuNIgAC_Q8AAn7EEVD5HDWAG_q_GTYE"
    )
    return
