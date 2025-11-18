import logging
from telegram import Update
from telegram.ext import ContextTypes

async def inlab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports who is currently in the lab."""

    if not context.bot_data['config']['Features']['NocoDBIntegration']:
        return

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/inlab - User without username attempted to use /inlab command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return

    # Load the EagleAPI and NocoDB clients from bot data
    eagle_api = context.bot_data["eagle_api"]
    nocodb = context.bot_data["nocodb"]

    # Call EagleAPI client; expected structure: {'people': [emails], 'count': n}
    inlab_data = eagle_api.inlab()

    # Convert emails to NocoDB usernames/tags using the nocodb helper
    tags = [
        nocodb.username_from_email(email)
        for email in inlab_data['people']
    ]

    # Log the in-lab data for debugging
    logging.info(f"commands/inlab - User @{username} requested correctly in-lab data: {inlab_data}")

    # Reply with a message depending on the count
    if inlab_data['count'] == 0:
        await update.message.reply_html("Nobody is in the lab right now.")
    else:
        await update.message.reply_html(
            f"There are <b>{inlab_data['count']}</b> people in the lab: {', '.join(tags)}"
        )
    return
