import os
import logging
from modules.nocodb import NocoDB
from modules.api_client import EagleAPI
from telegram import Update, ForceReply, BotCommand
from telegram.ext import Application, CommandHandler, ContextTypes

# Environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") # Telegram bot token
NOCO_URL = os.getenv("NOCO_URL")  # e.g. localhost:8080
NOCO_API_KEY = os.getenv("NOCO_API_KEY")  # x-token header value (api key)
EAGLE_API_URL = os.getenv("EAGLE_API_URL")  # e.g. api.eagletrt.it

# Create global instances of NocoDB and EagleAPI
nocodb = None
eagle_api = None

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

file_handler = logging.FileHandler("/data/bot.log", mode="a", encoding="utf-8")
file_handler.setLevel(logging.WARNING, logging.ERROR)
file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

logging.basicConfig(level=logging.INFO, handlers=[console_handler, file_handler])

# TODO:
# tag_cache = {
#     "areas": nocodb.area_tags(),
#     "workgroups": nocodb.workgroup_tags(),
#     "projects": nocodb.project_tags(),
#     "roles": nocodb.role_tags()
# }
def reply(msg):
    # Check nocodb tags
    for tag in utils.find_tags(text.lower()):
        if tag in tag_cache["areas"]:
            members = nocodb.area_members(tag.lstrip('@'))
        elif tag in tag_cache["workgroups"]:
            members = nocodb.workgroup_members(tag.lstrip('@'))
        elif tag in tag_cache["projects"]:
            members = nocodb.project_members(tag.lstrip('@'))
        elif tag in tag_cache["roles"]:
            members = nocodb.role_members(tag.lstrip('@'))
        else:
            continue

        if members:
            tag_list = ' '.join(members)
            bot.sendMessage(chatId, f"<b>{tag}</b>:\n{tag_list}",
                            reply_to_message_id=threadId, parse_mode='HTML')

    # odg show
    if text == "/odg" or text == "/todo":
        if not (odg := ODG.get(chatId=chatId, threadId=threadId)):
            odg = ODG(chatId=chatId, threadId=threadId)
        bot.sendMessage(chatId, f"📝 <b>Todo List</b>\n\n{odg}",
                        reply_to_message_id=threadId, parse_mode='HTML')

    # odg reset
    if text == "/odg reset" or text == "/todo reset":
        if odg := ODG.get(chatId=chatId, threadId=threadId):
            odg.reset()
        bot.setMessageReaction((chatId, msgId), [{'type': 'emoji', 'emoji': "🎉"}])

    # odg remove
    if text.startswith("/odg remove ") or text.startswith("/todo remove "):
        if not (odg := ODG.get(chatId=chatId, threadId=threadId)):
            odg = ODG(chatId=chatId, threadId=threadId)

        try:
            task_id = int(text.split(' ', 2)[2])
        except ValueError:
            bot.sendMessage(chatId, "❌ Task ID must be a number.", reply_to_message_id=threadId)
            return

        if (1 <= task_id <= odg.tasks.count()) and odg.remove_task(task_id-1):
            bot.setMessageReaction((chatId, msgId), [{'type': 'emoji', 'emoji': "👍"}])
        else:
            bot.sendMessage(chatId, f"❌ Task #{task_id} not found.", reply_to_message_id=threadId)

    # odg add
    if text.startswith("/odg ") or text.startswith("/todo "):
        if not (odg := ODG.get(chatId=chatId, threadId=threadId)):
            odg = ODG(chatId=chatId, threadId=threadId)

        task = Task(
            text=text.split(' ', 1)[1],
            created_by=msg['from'].get("first_name", "") + " " + msg['from'].get("last_name", ""),
            odg=odg
        )
        bot.setMessageReaction((chatId, msgId), [{'type': 'emoji', 'emoji': "✍"}])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )
    logging.info(f"/start requested by @{user.username}")

# TODO:
async def odg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    return

# FIXME: \n dopo i : (giusto ma non funziona)
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
            rf"<b>{inlab['count']} people in the lab:</b>\n{' '.join(tags)}",
            reply_markup=ForceReply(selective=True),
        )
    
    user = update.effective_user.username
    logging.info(f"/inlab requested by @{user}")

async def ore(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    username = update.effective_user.username
    
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
        rf"This month you've spent <b>{ore}</b> in the lab!",
        reply_markup=ForceReply(selective=True),
    )

    logging.info(f"/ore requested by @{username}")

async def tags(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_html(
        "#️⃣ <b>Tag List</b>\n\n"
        f"<b>Areas</b>\n{', '.join(tag_cache['areas'])}\n\n"
        f"<b>Workgroups</b>\n{', '.join(tag_cache['workgroups'])}\n\n"
        f"<b>Projects</b>\n{', '.join(tag_cache['projects'])}\n\n"
        f"<b>Roles</b>\n{', '.join(tag_cache['roles'])}",
        reply_markup=ForceReply(selective=True),
    )

    user = update.effective_user.username
    logging.info(f"/tags requested by @{user}")

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

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Validate environment variables and data directory
    if not NOCO_URL or not NOCO_API_KEY or not EAGLE_API_URL or not TOKEN:
        logging.error("Missing required environment variables: NOCO_URL, NOCO_API_KEY, BASE_ID, EAGLE_API_URL")
        exit(1)
    
    nocodb = NocoDB(NOCO_URL, NOCO_API_KEY)
    eagle_api = EagleAPI(EAGLE_API_URL)

    main()
    logging.info("T.E.C.S. ended")