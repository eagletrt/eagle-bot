import os  # For reading environment variables and filesystem paths
import logging  # Standard logging
from modules.nocodb import NocoDB  # Wrapper client for NocoDB (project-specific)
from modules.api_client import EagleAPI  # Wrapper client for Eagle API (project-specific)
from modules.database import ODG, Task  # ORM entities (using Pony ORM)
from pony.orm import db_session  # Pony ORM context manager for DB sessions
from telegram import Update, BotCommand  # Telegram types
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters  # Telegram bot framework
import re  # Regular expressions for mention parsing

# Environment variables expected by the bot:
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Telegram bot token
NOCO_URL = os.getenv("NOCO_URL")  # NocoDB base URL (e.g. localhost:8080)
NOCO_API_KEY = os.getenv("NOCO_API_KEY")  # API key for NocoDB (x-token header)
EAGLE_API_URL = os.getenv("EAGLE_API_URL")  # E-Agle API base URL (e.g. api.eagletrt.it)

# Global clients are created at startup and stored here for handlers to use
nocodb = None
eagle_api = None

# Cached tag lists fetched from NocoDB at startup to avoid repeated network calls
tag_cache = {}

# Color codes used for coloring log output in console only
COLORS = {
    "INFO": "\033[94m",     # Blue
    "WARNING": "\033[33m",  # Orange/yellow
    "ERROR": "\033[91m",    # Red
    "RESET": "\033[0m"      # Reset color
}

# Custom log formatter classes:
# Base ColorFormatter - kept here to allow extension if needed (currently does no extra formatting)
class ColorFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        return message


# BracketColorFormatter - colors only the "[LEVELNAME]" substring in the formatted log message.
# This keeps timestamps and the rest of the message uncolored when printed to the console.
class BracketColorFormatter(ColorFormatter):
    def format(self, record):
        message = super().format(record)
        # Determine color for the level name and replace only the bracketed level text
        levelname = record.levelname
        color = COLORS.get(levelname, COLORS["RESET"])
        start = message.find(f"[{levelname}]")
        if start != -1:
            end = start + len(f"[{levelname}]")
            message = (
                message[:start]
                + f"{color}[{levelname}]{COLORS['RESET']}"
                + message[end:]
            )
        return message


# Configure logging handlers: console (colorized) and file (only WARNING+ written)
console_handler = logging.StreamHandler()
console_handler.setFormatter(BracketColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))

file_handler = logging.FileHandler("/data/bot.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])


# Command handler: /start
# Sends a greeting and logs who started the bot. Guards against edited messages and reactions.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.edited_message or update.message_reaction:
        return

    user = update.effective_user
    # Reply with an HTML-formatted mention of the user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!"
    )
    logging.info(f"/start requested by @{user.username}")


# Command handler: /odg (agenda / todo list)
# Uses Pony ORM models ODG and Task stored in modules.database.
# Supports subcommands:
#   /odg reset        -> reset the current ODG
#   /odg remove <id>  -> remove a task by ID (1-based as shown to users)
#   /odg <task text>  -> add a task
#   /odg              -> show current todo list
async def odg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.edited_message or update.message_reaction:
        return

    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id
    text = update.message.text
    # Remove bot mention if present and trim whitespace
    text = text.replace("@eagletrtbot", "").strip()

    # Use a DB session so Pony ORM operations are within a transaction/context
    with db_session:
        # Fetch existing ODG for this chat/thread or create a new one
        if not (odg := ODG.get(chatId=chat_id, threadId=thread_id)):
            odg = ODG(chatId=chat_id, threadId=thread_id)

        # Reset ODG to empty
        if update.message.text.startswith("/odg reset"):
            odg.reset()
            return await update.message.set_reaction("👍")
        # Remove a task by its shown ID (user-provided). Convert to zero-based index for internal store.
        elif update.message.text.startswith("/odg remove"):
            try:
                task_id = int(update.message.text.split(' ', 2)[2])
            except (ValueError, IndexError):
                # If parsing failed, notify the user
                return await update.message.reply_text("Task ID must be a number.")

            # remove_task expects zero-based index; if removal was successful react with thumbs up
            if odg.remove_task(task_id-1):
                return await update.message.set_reaction("👍")
            else:
                return await update.message.reply_text(f"Task #{task_id} not found in the todo list.")
        # Add a new task. The user-provided text follows the command (/odg <text>)
        elif update.message.text.startswith("/odg "):
            Task(
                text=text.split(' ', 1)[1],
                created_by=(getattr(update.effective_user, "first_name", "") or "") + " " + (getattr(update.effective_user, "last_name", "") or ""),
                odg=odg
            )
            # React with a pencil emoji to indicate task created
            return await update.message.set_reaction("✍")
        # Default: show the todo list, formatted as HTML
        else:
            return await update.message.reply_html(
                f"📝 <b>Todo List</b>\n\n{odg}"
            )


# Command handler: /inlab
# Uses eagle_api and nocodb to report who is currently in the lab.
async def inlab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.edited_message or update.message_reaction:
        return

    # Call EagleAPI client; expected structure: {'people': [emails], 'count': n}
    inlab = eagle_api.inlab()
    # Convert emails to NocoDB usernames/tags using the nocodb helper
    tags = [
        nocodb.username_from_email(email)
        for email in inlab['people']
    ]
    # Reply with a message depending on the count
    if inlab['count'] == 0:
        await update.message.reply_text("The lab is currently empty :(")
    else:
        await update.message.reply_html(
            f"<b>{inlab['count']} people in the lab:</b>\n{' '.join(tags)}"
        )

    user = update.effective_user.username
    logging.info(f"/inlab requested by @{user}")


# Command handler: /ore
# Reports how many hours the invoking user has spent in the lab this month.
# Requires the Telegram user to have a username that maps to a NocoDB email.
async def ore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.edited_message or update.message_reaction:
        return

    username = update.effective_user.username

    # Telegram username is required to map to NocoDB
    if not username:
        await update.message.reply_text("You need a Telegram username to use this command.")
        return

    # Look up the user's email via NocoDB; this project stores mappings
    team_email = nocodb.email_from_username(username)
    if not team_email:
        await update.message.reply_text("You are not registered in the NocoDB database.")
        return

    # Local helper to format hours (float) into a human friendly string
    def pretty_time(hours: float) -> str:
        int_hours = int(hours)
        minutes = int((hours - int_hours) * 60)
        if hours < 1:
            return f"{minutes} minutes"
        return f"{int_hours}h {minutes}min"

    # Query EagleAPI for hours and pretty-print
    ore = eagle_api.oreLab(team_email.split('@')[0])
    ore = pretty_time(ore['ore'])

    await update.message.reply_html(
        rf"This month you've spent <b>{ore}</b> in the lab!"
    )

    logging.info(f"/ore requested by @{username}")


# Command handler: /tags
# Replies with cached lists of tags (areas, workgroups, projects, roles) fetched from NocoDB at startup.
async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.edited_message or update.message_reaction:
        return

    await update.message.reply_html(
        "#️⃣ <b>Tag List</b>\n\n"
        f"<b>Areas</b>\n{', '.join(tag_cache['areas'])}\n\n"
        f"<b>Workgroups</b>\n{', '.join(tag_cache['workgroups'])}\n\n"
        f"<b>Projects</b>\n{', '.join(tag_cache['projects'])}\n\n"
        f"<b>Roles</b>\n{', '.join(tag_cache['roles'])}"
    )

    user = update.effective_user.username
    logging.info(f"/tags requested by @{user}")


# Message handler: mention_handler
# Searches message text for mentions of the form @tag and replies with the member list for that tag.
# Special mention @inlab triggers the inlab() command handler.
async def mention_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.edited_message or update.message_reaction:
        return

    msg = update.message
    # Guard: skip if there's no text (e.g. stickers, images)
    if not msg or not msg.text:
        return

    text = msg.text.lower()
    # Find all mentions like @username or @tag (letters, digits, underscore, dot, hyphen allowed)
    found_tags = set(re.findall(r'@[\w\.-]+', text))
    if not found_tags:
        return

    # Iterate found tags and handle each; replies the list of members for matched tags
    for tag in found_tags:
        if tag == "@inlab":
            # If @inlab present, call the dedicated handler to show people in the lab
            return await inlab(update, context)
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

        # If members found, reply with an HTML-formatted list
        if members:
            tag_list = ' '.join(members)
            await msg.reply_html(f"<b>{tag}</b>:\n{tag_list}")


# Post-init hook: ps(application)
# Called after Application is built to set the bot's command list visible in Telegram clients.
async def ps(application: Application) -> None:
    commands = [
        BotCommand("start", "Start bot"),
        BotCommand("odg", "Show ODG"),
        BotCommand("inlab", "People currently in lab"),
        BotCommand("ore", "Your month's lab hours"),
        BotCommand("tags", "List available tags"),
    ]
    await application.bot.set_my_commands(commands)


# Main entrypoint that constructs and runs the Telegram Application (bot).
def main() -> None:
    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(ps)  # Register the post-init function to set commands
        .build()
    )

    logging.info("T.E.C.S. started")

    # Register command handlers for the bot
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("odg", odg))
    application.add_handler(CommandHandler("inlab", inlab))
    application.add_handler(CommandHandler("ore", ore))
    application.add_handler(CommandHandler("tags", tags))

    # Message handler for text messages that are not commands (to detect @mentions)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_handler))

    # Start polling for updates. allowed_updates=Update.ALL_TYPES ensures the bot receives all update kinds.
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# If run as script, validate environment and initialize clients and caches before starting main()
if __name__ == "__main__":
    # Validate presence of required environment variables. If any missing, log and exit.
    if not NOCO_URL or not NOCO_API_KEY or not EAGLE_API_URL or not TOKEN:
        logging.error("Missing required environment variables: NOCO_URL, NOCO_API_KEY, EAGLE_API_URL, TELEGRAM_BOT_TOKEN")
        exit(1)

    # Initialize NocoDB and Eagle clients for use by handlers
    nocodb = NocoDB(NOCO_URL, NOCO_API_KEY)
    eagle_api = EagleAPI(EAGLE_API_URL)
    # Populate tag_cache by fetching tag lists from NocoDB once at startup
    tag_cache = {
        "areas": nocodb.area_tags(),
        "workgroups": nocodb.workgroup_tags(),
        "projects": nocodb.project_tags(),
        "roles": nocodb.role_tags()
    }

    # Run the bot
    main()
    logging.info("T.E.C.S. ended")
