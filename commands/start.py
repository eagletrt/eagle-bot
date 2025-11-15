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
        return await update.message.reply_html("You need a Telegram username to use this command.")

    logging.info(f"commands/start - User @{username} started the bot")
    return await update.message.reply_sticker(
        sticker="CAACAgQAAxkBAAE94hJpGMjqZi9VR1ee2gbzFw7POwuNIgAC_Q8AAn7EEVD5HDWAG_q_GTYE"
    )
