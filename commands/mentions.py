import logging
import re
import asyncio
from telegram import Update
from telegram.ext import ContextTypes

async def mention_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles mentions of tags and replies with member lists."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/mentions - User without username attempted to use mention handler")
        return

    # Guard: skip if there's no text
    msg = update.message
    if not msg or (not msg.text and not msg.caption):
        logging.info(f"commands/mentions - Message from @{username} has no text or caption to process.")
        return
    
    # Find all mentions like @username or @tag (letters, digits, underscore, dot, hyphen allowed)
    text = msg.text.lower() if msg.text else msg.caption.lower()
    found_tags = set(re.findall(r'@[\w\.-]+', text))
    if not found_tags:
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/mentions - Unauthorized /mentions attempt by @{username}")
        return

    # Load Database and tag cache from bot data
    database = context.bot_data["database"]
    tag_cache = context.bot_data["tag_cache"]
    whitelist = context.bot_data["whitelist"]

    message = ""
    temp_message = None

    if "@inlab" in found_tags and context.bot_data['config']['Features']['InLabIntegration'] and context.bot_data['config']['Features']['DatabaseIntegration']:
        temp_message = await update.message.reply_html("Dame n’atimo che i cato fora")

    # Iterate found tags and handle each; replies the list of members for matched tags
    for tag in found_tags:
        tag_name = tag[1:] # Remove '@'

        if tag_name == "inlab":

            # Check if InLab integration is enabled
            if not context.bot_data['config']['Features']['InLabIntegration']:
                logging.warning(f"commands/mentions - InLab integration is disabled; cannot process @inlab request from @{username}")
                return
            
            # Load the InLab from bot data
            inlabClient = context.bot_data["inlabClient"]

            # Call InLab client; expected structure: {'people': [emails], 'count': n}
            inlab_data = inlabClient.inlab()

            # Convert emails to Database usernames/tags using the database helper
            tags = await asyncio.gather(*[
                database.username_from_email(email)
                for email in inlab_data
            ])

            if len(inlab_data) == 0:
                members = []
            else:
                members = tags
        elif tag in tag_cache['areas'] or tag in tag_cache['workgroups'] or tag in tag_cache['projects'] or tag in tag_cache['roles']:
            members = whitelist.members_cache(tag)
        else:
            members = None

        logging.info(f"commands/mentions - User @{username} requested correctly members for tag {tag}: {members}")

        # If members found, reply with an HTML-formatted list
        if members:
            tag_list = ' '.join(members)
            message = message + f"<b>{tag}</b>:\n{tag_list}\n\n"
        
    # If we have a message to send, reply with it
    if message != "":
        if temp_message:
            await temp_message.edit_text(message, parse_mode='HTML')
        else:
            await update.message.reply_html(message)
    elif temp_message:
        await temp_message.edit_text("Nobody is in the lab right now.", parse_mode='HTML')
    return