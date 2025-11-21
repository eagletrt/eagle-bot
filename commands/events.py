import logging
from pony.orm import db_session
from modules.quiz import Events
from telegram import Update
from telegram.ext import ContextTypes

async def events(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Lists all available events in the database."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/events - User without username attempted to use /events command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['Quiz']):
        logging.warning(f"commands/events - Unauthorized /events attempt by @{username}")
        return
    
    # Fetch all events and format them into a list for the reply
    with db_session:
        event_list = Events.select().order_by(Events.event_id)
        if not event_list:
            logging.error(f"commands/events - No events found for user @{username}")
            await update.message.reply_html("No events found in the database.")
            return
    
        event_texts = []
        for e in event_list:
            event_texts.append(f"<code>/event {e.event_id}</code> - {e.short_name}")
    
    logging.info(f"commands/events - User @{username} requested correctly the list of available events")
    await update.message.reply_html(
        f"<b>Available Events:</b>\n" + "\n".join(event_texts)
    )
    return
