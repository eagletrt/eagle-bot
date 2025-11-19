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
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/qr - Unauthorized /qr attempt by @{username}")
        return

    # Guard: skip if there's no text (e.g. stickers, images)
    msg = update.message
    if not msg or not msg.text:
        logging.info(f"Message from @{username} has no text to process.")
        return

    # Find all mentions like @username or @tag (letters, digits, underscore, dot, hyphen allowed)
    text = msg.text.lower()
    found_tags = set(re.findall(r'@[\w\.-]+', text))
    if not found_tags:
        return

    # Load NocoDB and tag cache from bot data
    nocodb = context.bot_data["nocodb"]
    tag_cache = context.bot_data["tag_cache"]

    message = f""

    # Iterate found tags and handle each; replies the list of members for matched tags
    for tag in found_tags:
        tag_name = tag[1:] # Remove '@'

        if tag_name == "inlab":

            # Check if EagleAPI integration is enabled
            if not context.bot_data['config']['Features']['EAgleAPIIntegration']:
                logging.warning(f"commands/mentions - EagleAPI integration is disabled; cannot process @inlab request from @{username}")
                return
            
            # Load the EagleAPI from bot data
            eagle_api = context.bot_data["eagle_api"]

            # Call EagleAPI client; expected structure: {'people': [emails], 'count': n}
            inlab_data = eagle_api.inlab()

            # Convert emails to NocoDB usernames/tags using the nocodb helper
            tags = await asyncio.gather(*[
                nocodb.username_from_email(email)
                for email in inlab_data['people']
            ])

            if inlab_data['count'] == 0:
                members = []
            else:
                members = tags
        elif tag in tag_cache.get("areas", []):
            members = await nocodb.members(tag.lstrip('@'), "area")
        elif tag in tag_cache.get("workgroups", []):
            members = await nocodb.members(tag.lstrip('@'), "workgroup")
        elif tag in tag_cache.get("projects", []):
            members = await nocodb.members(tag.lstrip('@'), "project")
        elif tag in tag_cache.get("roles", []):
            members = await nocodb.members(tag.lstrip('@'), "role")
        else:
            members = None

        logging.info(f"commands/mentions - User @{username} requested correctly members for tag {tag}: {members}")

        # If members found, reply with an HTML-formatted list
        if members:
            tag_list = ' '.join(members)
            message = message + f"<b>{tag}</b>:\n{tag_list}\n\n"
        
    # If we have a message to send, reply with it
    if message != "":
        await update.message.reply_html(message)
    return