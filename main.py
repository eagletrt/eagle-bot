import os
import logging
from modules.nocodb import NocoDB
from modules.api_client import EagleAPI
from modules.database import ODG, Task
from pony.orm import db_session
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import re

# FIXME: handle message modifications and deletions

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Telegram bot token
NOCO_URL = os.getenv("NOCO_URL")  # e.g. localhost:8080
NOCO_API_KEY = os.getenv("NOCO_API_KEY")  # x-token header value (api key)
EAGLE_API_URL = os.getenv("EAGLE_API_URL")  # e.g. api.eagletrt.it

# Create global instances of NocoDB and EagleAPI
nocodb = None
eagle_api = None
tag_cache = {}

# Custom log color
COLORS = {
    "INFO": "\033[94m",     # Blue
    "WARNING": "\033[33m",  # Orange
    "ERROR": "\033[91m",    # Red
    "RESET": "\033[0m"
}

# Custom log formatter to color only the [LEVELNAME] part
class ColorFormatter(logging.Formatter):
    def format(self, record):
        message = super().format(record)
        return message
    
class BracketColorFormatter(ColorFormatter):
    def format(self, record):
        message = super().format(record)
        # Color only what is inside the square brackets [LEVELNAME]
        levelname = record.levelname
        color = COLORS.get(levelname, COLORS["RESET"])
        # Find the position of [LEVELNAME] and color only that
        start = message.find(f"[{levelname}]")
        if start != -1:
            end = start + len(f"[{levelname}]")
            message = (
                message[:start]
                + f"{color}[{levelname}]{COLORS['RESET']}"
                + message[end:]
            )
        return message
    
console_handler = logging.StreamHandler()
console_handler.setFormatter(BracketColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))

file_handler = logging.FileHandler("./data/bot.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.WARNING)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!"
    )
    logging.info(f"/start requested by @{user.username}")

# FIXME: React to the message (not send)
async def odg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    thread_id = update.effective_message.message_thread_id
    text = update.message.text
    text = text.replace("@eagletrtbot", "").strip()

    with db_session:
        # Cerca ODG esistente, altrimenti crealo
        if not (odg := ODG.get(chatId=chat_id, threadId=thread_id)):
            odg = ODG(chatId=chat_id, threadId=thread_id)

        if update.message.text.startswith("/odg reset"):
            odg.reset()
            return await update.message.reply_text("👍", reply_to_message_id=update.message.message_id)
        elif update.message.text.startswith("/odg remove"):
            try:
                task_id = int(update.message.text.split(' ', 2)[2])
            except (ValueError, IndexError):
                return await update.message.reply_text("Task ID must be a number.")
            
            if odg.remove_task(task_id-1):
                return await update.message.reply_text("👍", reply_to_message_id=update.message.message_id)
            else:
                return await update.message.reply_text(f"Task #{task_id} not found in the todo list.")
        elif update.message.text.startswith("/odg "):
            Task(
                text=text.split(' ', 1)[1],
                created_by=(getattr(update.effective_user, "first_name", "") or "") + " " + (getattr(update.effective_user, "last_name", "") or ""),
                odg=odg
            )
            return await update.message.reply_text("✍️", reply_to_message_id=update.message.message_id)
        else:
            return await update.message.reply_html(
                f"📝 <b>Todo List</b>\n\n{odg}"
            )

async def inlab(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    inlab = eagle_api.inlab()
    tags = [
        nocodb.username_from_email(email)
        for email in inlab['people']
    ]
    if inlab['count'] == 0:
        await update.message.reply_text("The lab is currently empty :(")
    else:
        await update.message.reply_html(
            f"<b>{inlab['count']} people in the lab:</b>\n{' '.join(tags)}"
        )
    
    user = update.effective_user.username
    logging.info(f"/inlab requested by @{user}")

async def ore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username

    if not username:
        await update.message.reply_text("You need a Telegram username to use this command.")
        return
    
    team_email = nocodb.email_from_username(username)
    if not team_email:
        await update.message.reply_text("You are not registered in the NocoDB database.")
        return
    
    def pretty_time(hours: float) -> str:
        int_hours = int(hours)
        minutes = int((hours - int_hours) * 60)
        if hours < 1:
            return f"{minutes} minutes"
        return f"{int_hours}h {minutes}min"

    ore = eagle_api.oreLab(team_email.split('@')[0])
    ore = pretty_time(ore['ore'])

    await update.message.reply_html(
        rf"This month you've spent <b>{ore}</b> in the lab!"
    )

    logging.info(f"/ore requested by @{username}")

async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "#️⃣ <b>Tag List</b>\n\n"
        f"<b>Areas</b>\n{', '.join(tag_cache['areas'])}\n\n"
        f"<b>Workgroups</b>\n{', '.join(tag_cache['workgroups'])}\n\n"
        f"<b>Projects</b>\n{', '.join(tag_cache['projects'])}\n\n"
        f"<b>Roles</b>\n{', '.join(tag_cache['roles'])}"
    )

    user = update.effective_user.username
    logging.info(f"/tags requested by @{user}")

async def mention_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg or not msg.text:
        return

    text = msg.text.lower()
    found_tags = set(re.findall(r'@[\w\.-]+', text))
    if not found_tags:
        return

    for tag in found_tags:
        if tag in tag_cache.get("areas", []):
            members = nocodb.members(tag.lstrip('@'), "area")
        elif tag in tag_cache.get("workgroups", []):
            members = nocodb.members(tag.lstrip('@'), "workgroup")
        elif tag in tag_cache.get("projects", []):
            members = nocodb.members(tag.lstrip('@'), "project")
        elif tag in tag_cache.get("roles", []):
            members = nocodb.members(tag.lstrip('@'), "role")
        else:
            members = None

        if members:
            tag_list = ' '.join(members)
            await msg.reply_html(f"<b>{tag}</b>:\n{tag_list}")

async def ps(application: Application) -> None:
    # Set bot commands for the Telegram interface
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("odg", "Show the todo list"),
        BotCommand("inlab", "Show who is currently in the lab"),
        BotCommand("ore", "Show how many hours you spent in the lab this month"),
        BotCommand("tags", "Show the list of available tags"),
    ]
    await application.bot.set_my_commands(commands)

def main() -> None:

    application = (
        Application.builder()
        .token(TOKEN)
        .post_init(ps)
        .build()
    )

    logging.info("T.E.C.S. started")

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("odg", odg))
    application.add_handler(CommandHandler("inlab", inlab))
    application.add_handler(CommandHandler("ore", ore))
    application.add_handler(CommandHandler("tags", tags))
    
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_handler))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Validate environment variables and data directory
    if not NOCO_URL or not NOCO_API_KEY or not EAGLE_API_URL or not TOKEN:
        logging.error("Missing required environment variables: NOCO_URL, NOCO_API_KEY, BASE_ID, EAGLE_API_URL")
        exit(1)
    
    nocodb = NocoDB(NOCO_URL, NOCO_API_KEY)
    eagle_api = EagleAPI(EAGLE_API_URL)
    tag_cache = {
        "areas": nocodb.area_tags(),
        "workgroups": nocodb.workgroup_tags(),
        "projects": nocodb.project_tags(),
        "roles": nocodb.role_tags()
    }

    main()
    logging.info("T.E.C.S. ended")