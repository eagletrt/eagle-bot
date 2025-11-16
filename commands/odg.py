import logging
from pony.orm import db_session
from modules.database import ODG, Task
from telegram import Update
from telegram.ext import ContextTypes

async def odg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /odg command for managing the agenda."""

    # Check if the command is used in a message context
    if update.edited_message or update.message_reaction:
        return
    
    # Ensure the user has a Telegram username
    username = update.effective_user.username
    if not username:
        logging.warning("commands/odg - User without username attempted to use /odg command")
        await update.message.reply_html("You need a Telegram username to use this command.")
        return

    # Get chat and thread identifiers
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id

    # Remove bot mention if present and trim whitespace
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    with db_session:
        # Fetch existing ODG for this chat/thread or create a new one
        if not (odg := ODG.get(chatId=chat_id, threadId=thread_id)):
            odg = ODG(chatId=chat_id, threadId=thread_id)

        # Reset ODG to empty
        if update.message.text.startswith("/odg reset"):
            odg.reset()
            logging.info(f"commands/odg - User @{username} reset the ODG in chat {chat_id} thread {thread_id}")
            await update.message.set_reaction("👍")
        
        # Remove a task by its shown ID (user-provided). Convert to zero-based index for internal store.
        elif update.message.text.startswith("/odg remove"):
            try:
                task_id = int(update.message.text.split(' ', 2)[2])
            except (ValueError, IndexError):

                # If parsing failed, notify the user
                logging.warning(f"commands/odg - User @{username} provided invalid task ID for removal in chat {chat_id} thread {thread_id}")
                await update.message.reply_text("Task ID must be a number.")
                return

            # remove_task expects zero-based index; if removal was successful react with thumbs up
            if odg.remove_task(task_id-1):
                logging.info(f"commands/odg - User @{username} removed task #{task_id} from the ODG in chat {chat_id} thread {thread_id}")
                await update.message.set_reaction("👍")
            else:
                logging.warning(f"commands/odg - User @{username} attempted to remove non-existent task #{task_id} from the ODG in chat {chat_id} thread {thread_id}")
                await update.message.reply_text(f"Task #{task_id} not found in the todo list.")
            
        # Add a new task. The user-provided text follows the command (/odg <text>)
        elif update.message.text.startswith("/odg "):
            Task(
                text=text.split(' ', 1)[1],
                created_by=(getattr(update.effective_user, "first_name", "") or "") + " " + (getattr(update.effective_user, "last_name", "") or ""),
                odg=odg
            )

            # React with a pencil emoji to indicate task created
            logging.info(f"commands/odg - User @{username} added a new task to the ODG in chat {chat_id} thread {thread_id}")
            await update.message.set_reaction("✍")
        
        # Default: show the todo list, formatted as HTML
        else:
            logging.info(f"commands/odg - User @{username} requested the ODG in chat {chat_id} thread {thread_id}")
            await update.message.reply_html(
                f"📝 <b>Todo List</b>\n\n{odg}"
            )
            
        return
