import logging
from pony.orm import db_session
from modules.quiz import Events
from telegram import Update
from telegram.ext import ContextTypes

async def event(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetches and displays details for a specific event."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("User without username attempted to use /event command")
        return await update.message.reply_html("You need a Telegram username to use this command.")
    
    # Whitelist check
    if username not in context.bot_data['config']['Whitelist']['QuizDB']:
        logging.warning(f"commands/event - Unauthorized /event attempt by @{username}")
        return
    
    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()
    
    # Extract event ID from the command text
    id = text.split(' ', 1)[1] if ' ' in text else None

    if not id:
        logging.info(f"commands/event - No event ID provided by @{username}")
        return await update.message.reply_html("Please specify an event ID. Usage: /event &lt;id&gt;")
    
    # Fetch the event from the database and reply with its details
    with db_session:
        event_entity = Events.get(event_id=id)
        if not event_entity:
            logging.info(f"commands/event - Event with ID {id} not found for user @{username}")
            return await update.message.reply_html(f"Event with ID {id} not found.")
    
    logging.info(f"commands/event - User @{username} requested correctly details for event ID {event_entity.event_id}")
    return await update.message.reply_html(
        f"<b>Event ID {event_entity.event_id} - {event_entity.short_name}</b>\n"
        f"Name: {event_entity.event_name}\n"
        f"Country: {event_entity.country}\n"
        f"Website: {event_entity.website}"
    )
