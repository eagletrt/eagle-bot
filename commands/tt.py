import logging
from telegram import Update
from telegram.ext import ContextTypes

async def tt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an animation of TermoTomas when the /tt command is used."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/tt - User without username attempted to use /tt command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/tt - Unauthorized /tt attempt by @{username}")
        return

    logging.info(f"commands/tt - User @{username} used the /tt command")
    await update.message.reply_photo(
        photo="AgACAgQAAxkBAAFYPbFrBWnYD-vEml3blApr7rvH-ykqlAACqBJrGxoeKFBV8QiYPpH4igEAAwIAA3kAAz0E",
        caption=f"@{username} summoned TermoTomas ❤️‍🔥"
    )
    return
