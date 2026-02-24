import logging
import requests
from telegram import Update
from telegram.ext import ContextTypes

async def no(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message from the NAAS API and logs who used the /no command."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/no - User without username attempted to use /no command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/no - Unauthorized /no attempt by @{username}")
        return

    url = context.bot_data['config']['Settings']['NAAS_API_URL']
    response = requests.get(url, timeout=5).json()

    logging.info(f"commands/no - User @{username} used the /no command")
    await update.message.reply_html(f"@{username} wanted to say:\n{response['reason']}")
    return
