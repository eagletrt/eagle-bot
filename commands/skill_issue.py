import logging
from telegram import Update
from telegram.ext import ContextTypes

async def skillIssue(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a skill issue message and logs who triggered it."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/skill_issue - User without username attempted to use /skill_issue command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/skill_issue - Unauthorized /skill_issue attempt by @{username}")
        return

    logging.info(f"commands/skill_issue - User @{username} triggered skill issue")
    await update.message.reply_sticker(
        sticker="CAACAgQAAxkBAAFDR1lpoFgFPvS8LtfYDWfOSVLz_YUeZQACyB4AArrXYFLdjroFLR2yvjoE"
    )
    return
