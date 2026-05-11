import logging
from telegram import Update
from telegram.ext import ContextTypes
import asyncio

async def inlab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reports who is currently in the lab."""

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
        logging.warning(f"commands/inlab - Unauthorized /inlab attempt by @{username}")
        return

    # Load the InLab and Database clients from bot data
    inlabClient = context.bot_data["inlabClient"]
    database = context.bot_data["database"]

    # Send temporary message
    message = await update.message.reply_html("Dame n’atimo che i cato fora")

    # Call InLab client; expected structure: {'people': [emails], 'count': n}
    inlab_data = inlabClient.inlab()

    # Convert emails to Database usernames/tags using the database helper
    tags = await asyncio.gather(
        *[database.username_from_email(email) for email in inlab_data]
    )

    # Log the in-lab data for debugging
    logging.info(f"commands/inlab - User @{username} requested correctly in-lab data: {inlab_data}")

    # Reply with a message depending on the count
    if len(inlab_data) == 0:
        await message.edit_text("Nobody is in the lab right now.", parse_mode='HTML')
    else:
        await message.edit_text(
            f"There are <b>{len(inlab_data)}</b> people in the lab: \n{' '.join(tags)}",
            parse_mode='HTML'
        )
    return
