import logging
from modules.odg import get_or_create_odg, format_odgdocs
from telegram import Update
from telegram.ext import ContextTypes

async def odgdocs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /odgdocs command that return a copy paste ready version of the ODG for the docs."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/odgdocs - User without username attempted to use /odgdocs command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/odgdocs - Unauthorized /odgdocs attempt by @{username}")
        return

    # Get chat and thread identifiers
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id

    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    # Fetch existing ODG for this chat/thread or create a new one
    odg_id = get_or_create_odg(chat_id, thread_id)
    
    logging.info(f"commands/odgdocs - User @{username} requested the ODG in chat {chat_id} thread {thread_id}")
    await update.message.reply_html(
        f"<b>Agenda</b>\n\n{format_odgdocs(odg_id)}"
    )
    return
