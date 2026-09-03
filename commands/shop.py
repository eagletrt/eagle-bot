import logging
from modules.shop import get_or_create_shop, reset_shop, remove_item, add_item, format_shop
from telegram import Update
from telegram.ext import ContextTypes

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /shop command for managing the shopping list."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/shop - User without username attempted to use /shop command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return
    
    # Whitelist check
    if context.bot_data['config']['Features']['Whitelist'] and not context.bot_data['whitelist'].is_user_whitelisted(username, context.bot_data['config']['Whitelist']['General']):
        logging.warning(f"commands/shop - Unauthorized /shop attempt by @{username}")
        return

    # Get chat and thread identifiers
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id

    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    # Fetch existing SHOP for this chat/thread or create a new one
    shop_id = get_or_create_shop(chat_id, thread_id)

    # Reset SHOP to empty
    if text.lower().startswith("/shop reset"):
        reset_shop(shop_id)
        logging.info(f"commands/shop - User @{username} reset the shop list in chat {chat_id} thread {thread_id}")
        await update.message.set_reaction("👍")
        return
    
    # Remove an item by its shown ID (user-provided). Convert to zero-based index for internal store.
    elif text.lower().startswith("/shop remove"):
        try:
            item_id = int(text.split(' ', 2)[2])
        except (ValueError, IndexError):

            # If parsing failed, notify the user
            logging.warning(f"commands/shop - User @{username} provided invalid item ID for removal in chat {chat_id} thread {thread_id}")
            await update.message.reply_text("Item ID must be a number.")
            return

        if item_id < 1:
            logging.warning(f"commands/shop - User @{username} provided invalid item ID for removal in chat {chat_id} thread {thread_id}")
            await update.message.reply_text("Item ID must be a positive number.")
            return

        # remove_item expects zero-based index; if removal was successful react with thumbs up
        if remove_item(shop_id, item_id-1):
            logging.info(f"commands/shop - User @{username} removed item #{item_id} from the shop list in chat {chat_id} thread {thread_id}")
            await update.message.set_reaction("👍")
        else:
            logging.warning(f"commands/shop - User @{username} attempted to remove non-existent item #{item_id} from the shop list in chat {chat_id} thread {thread_id}")
            await update.message.reply_text(f"Item #{item_id} not found in the shop list.")
        return
        
    # Add a new item. The user-provided text follows the command (/shop <text>)
    elif text.lower().startswith("/shop "):
        add_item(
            shop_id,
            text.split(' ', 1)[1],
            (getattr(update.effective_user, "first_name", "") or "") + " " + (getattr(update.effective_user, "last_name", "") or ""),
        )

        # React with a pencil emoji to indicate item created
        logging.info(f"commands/shop - User @{username} added a new item to the shop list in chat {chat_id} thread {thread_id}")
        await update.message.set_reaction("✍")
        return
    
    # Default: show the shop list, formatted as HTML
    else:
        logging.info(f"commands/shop - User @{username} requested the shop list in chat {chat_id} thread {thread_id}")
        await update.message.reply_html(
            f"🛒 <b>Shop List</b>\n\n{format_shop(shop_id)}"
        )
        return
