import logging
from telegram import Update
from telegram.ext import ContextTypes

async def eduardo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an animation of Eduardo when the /eduardo command is used."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/eduardo - User without username attempted to use /eduardo command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/eduardo - Unauthorized /eduardo attempt by @{username}")
        return

    logging.info(f"commands/eduardo - User @{username} used the /eduardo command")
    await update.message.reply_animation(
        animation="https://media1.tenor.com/m/BHbYLeXUf4QAAAAC/eduardo-cinco-noches-eduardo.gif",
        caption=f"@{username} summoned Eduardo!"
    )
    return
