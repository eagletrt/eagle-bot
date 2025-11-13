import os
import logging
import tomllib
from modules.nocodb import NocoDB
from modules.api_client import EagleAPI
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

# Import command handlers
from commands.start import start
from commands.odg import odg
from commands.inlab import inlab
from commands.ore import ore
from commands.tags import tags
from commands.mentions import mention_handler
from commands.quiz import quiz
from commands.quizzes import quizzes
from commands.event import event
from commands.events import events
from commands.question import question
from commands.answer import answer

# Color codes used for coloring log output in console only
COLORS = {
    "INFO": "\033[94m",
    "WARNING": "\033[33m",
    "ERROR": "\033[91m",
    "RESET": "\033[0m"
}

class ColorFormatter(logging.Formatter):
    """Custom logging formatter to add colors based on log level."""

    def format(self, record):
        """Format log messages with colors based on severity level."""

        message = super().format(record)
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

# Configure logging to console with colors
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))
logging.basicConfig(level=logging.INFO, handlers=[console_handler])

async def ps(application: Application) -> None:
    """Post-initialization hook to set bot commands."""

    commands = [
        BotCommand("odg", "Show ODG"),
        BotCommand("inlab", "People currently in lab"),
        BotCommand("ore", "Your month's lab hours"),
        BotCommand("tags", "List available tags"),
    ]

    # Conditional addition of quiz commands
    if application.bot_data["config"]['Features']['FSQuiz']:
        commands.extend([
            BotCommand("question", "Get a random question"),
        ])

    await application.bot.set_my_commands(commands)

def main() -> None:
    """Main function to set up and run the bot."""

    # Load configuration from config.ini
    with open("data/config.ini", "rb") as f:
        try:
            config = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            logging.error(f"main/main - Error parsing data/config.ini: {e}")
            exit(1)

    # Configure logging from config file
    log_level_console = config["Settings"]["ConsoleLogLevel"]
    log_level_file = config["Settings"]["FileLogLevel"]
    log_file_path = config["Paths"]["LogFilePath"]

    # Get the root logger and set its level
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level_console))

    # Add file handler
    file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
    file_handler.setLevel(getattr(logging, log_level_file))
    file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    root_logger.addHandler(file_handler)

    # Remove verbose logs (PTB)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)


    application = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .post_init(ps)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    logging.info("main/main - T.E.C.S. started")

    # Initialize clients and caches
    nocodb = NocoDB(config['Settings']['NOCO_URL'], os.getenv("NOCO_API_KEY"))
    eagle_api = EagleAPI(config['Settings']['EAGLE_API_URL'])
    tag_cache = {
        "areas": nocodb.tags('area'),
        "workgroups": nocodb.tags('workgroup'),
        "projects": nocodb.tags('project'),
        "roles": nocodb.tags('role'),
    }

    # Store clients and caches in bot_data for access in handlers
    application.bot_data["nocodb"] = nocodb
    application.bot_data["eagle_api"] = eagle_api
    application.bot_data["tag_cache"] = tag_cache
    application.bot_data["config"] = config
    logging.info("main/main - Clients and tag cache initialized and stored in bot_data.")

    # Register handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("odg", odg))
    application.add_handler(CommandHandler("inlab", inlab))
    application.add_handler(CommandHandler("ore", ore))
    application.add_handler(CommandHandler("tags", tags))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_handler))

    # Conditional registration of quiz-related handlers
    if config['Features']['FSQuiz']:
        application.add_handler(CommandHandler("quiz", quiz))
        application.add_handler(CommandHandler("quizzes", quizzes))
        application.add_handler(CommandHandler("event", event))
        application.add_handler(CommandHandler("events", events))
        application.add_handler(CommandHandler("question", question))
        application.add_handler(CommandHandler("answer", answer))
        logging.info("main/main - Quiz feature enabled and handlers registered.")

    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    # Validate environment variables
    required_vars = ["TELEGRAM_BOT_TOKEN", "NOCO_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        logging.error(f"main/main - Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)

    main()
    logging.info("main/main - T.E.C.S. ended")
