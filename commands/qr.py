import logging
from telegram import Update
from telegram.ext import ContextTypes

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ Generates a shlink QR code and sends it to the user. """

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/qr - User without username attempted to use /qr command")
        return await update.message.reply_html("You need a Telegram username to use this command.")
    
    # ...