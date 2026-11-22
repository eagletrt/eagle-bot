import logging
from telegram import Update
from telegram.ext import ContextTypes
from modules.quiz import log_poll_answer

async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Logs a user's answer to a non-anonymous quiz poll (FSQuizLogging)."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/poll_answer - User without username attempted to answer a poll")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/poll_answer - Unauthorized /poll_answer attempt by @{username}")
        return

    log_poll_answer(update.poll_answer.poll_id, update.poll_answer.user.username, update.poll_answer.option_ids[0])

    logging.info(f"commands/poll_answer - User @{update.poll_answer.user.username} answered poll {update.poll_answer.poll_id} with option {update.poll_answer.option_ids[0]}")
