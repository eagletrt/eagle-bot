import logging
from telegram import Update
from telegram.ext import ContextTypes

async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Replies with cached lists of tags."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/tags - User without username attempted to use /tags command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return

    # Access the tag cache from bot_data
    tag_cache = context.bot_data["tag_cache"]

    logging.info(f"commands/tags - User @{username} requested tag list")

    await update.message.reply_html(
        "#️⃣ <b>Tag List</b>\n\n"
        f"<b>Areas</b>\n{', '.join(tag_cache['areas'])}\n\n"
        f"<b>Workgroups</b>\n{', '.join(tag_cache['workgroups'])}\n\n"
        f"<b>Projects</b>\n{', '.join(tag_cache['projects'])}\n\n"
        f"<b>Roles</b>\n{', '.join(tag_cache['roles'])}"
    )
    return
