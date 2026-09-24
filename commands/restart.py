import logging
import os
from telegram import Update
from telegram.ext import ContextTypes

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Restarts the bot (requires admin privileges)."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/restart - User without username attempted to use /restart command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['Restart']):
        logging.warning(f"commands/restart - Unauthorized /restart attempt by @{username}")
        return

    logging.info(f"commands/restart - Restart initiated by @{username}")
    await update.message.reply_html("Restarting bot...")
    
    os._exit(0)
