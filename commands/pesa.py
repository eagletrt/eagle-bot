import logging
from telegram import Update
from telegram.ext import ContextTypes

async def pesa(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting and logs who started the bot."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/pesa - User without username attempted to use /pesa command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/pesa - Unauthorized /pesa attempt by @{username}")
        return
    
    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    msg = text if text.count(' ') >= 1 else None

    id = context.bot_data['config']['Settings']['PESA_CHAT_ID']

    if not msg:
        logging.warning(f"commands/pesa - User @{username} did not provide a message for /pesa command")
        await update.message.reply_text("Please provide a message to send. Usage: /pesa <message>")
        return

    logging.info(f"commands/pesa - User @{username} used the /pesa command")
    await update.message.set_reaction("👍")
    await context.bot.send_message(chat_id=id, text=f"@{username} wanted to say:\n{msg}")
    return
