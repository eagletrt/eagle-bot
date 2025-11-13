import logging
from telegram import Update
from telegram.ext import ContextTypes

async def inlab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports who is currently in the lab."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("User without username attempted to use /inlab command")
        return await update.message.reply_html("You need a Telegram username to use this command.")

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
        return await update.message.reply_html("Nobody is in the lab right now.")
    else:
        return await update.message.reply_html(
            f"There are <b>{inlab_data['count']}</b> people in the lab: {', '.join(tags)}"
        )
