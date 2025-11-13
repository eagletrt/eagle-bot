import logging
import re
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
        logging.warning("User without username attempted to use mention handler")
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
        logging.info(f"No tags found in message from @{username}: {text}")
        return

    # Load NocoDB and tag cache from bot data
    eagle_api = context.bot_data["eagle_api"]
    nocodb = context.bot_data["nocodb"]
    tag_cache = context.bot_data["tag_cache"]

    # Iterate found tags and handle each; replies the list of members for matched tags
    for tag in found_tags:
        tag_name = tag[1:] # Remove '@'

        if tag_name == "inlab":
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
        elif tag in tag_cache.get("areas", []):
            members = nocodb.members(tag.lstrip('@'), "area")
        elif tag in tag_cache.get("workgroups", []):
            members = nocodb.members(tag.lstrip('@'), "workgroup")
        elif tag in tag_cache.get("projects", []):
            members = nocodb.members(tag.lstrip('@'), "project")
        elif tag in tag_cache.get("roles", []):
            members = nocodb.members(tag.lstrip('@'), "role")
        else:
            members = None

        logging.info(f"commands/mentions - User @{username} requested correctly members for tag {tag}: {members}")

        # If members found, reply with an HTML-formatted list
        if members:
            tag_list = ' '.join(members)
            return await msg.reply_html(f"<b>{tag}</b>:\n{tag_list}")