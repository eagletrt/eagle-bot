import logging
from telegram import Update
from telegram.ext import ContextTypes

async def id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a greeting and logs who started the bot."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return

    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/id - User without username attempted to use /id command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return

    logging.info(f"commands/id - /id command used by @{username}")
    
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    thread_id = update.message.message_thread_id

    response_text = (
        f"<b>Chat/Group ID:</b> {chat_id}\n"
        f"<b>User ID:</b> {user_id}\n"
        f"<b>Username:</b> @{username}"
    )

    if thread_id:
        response_text += f"\n<b>Thread ID:</b> {thread_id}"

    await update.message.reply_html(response_text)

    return
