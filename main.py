import os
import logging
import tomllib
from modules.nocodb import NocoDB
from modules.api_client import EagleAPI
from modules.shlink import ShlinkAPI
from modules.whitelist import Whitelist
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, PollAnswerHandler, filters
from modules.scheduler import setup_scheduler

# Import command handlers
from commands.start import start
from commands.odg import odg
from commands.inlab import inlab
from commands.ore import ore
from commands.tags import tags
from commands.mentions import mention_handler
from commands.qr import qr
from commands.quiz import quiz
from commands.quizzes import quizzes
from commands.event import event
from commands.events import events
from commands.question import question
from commands.question_answer import question_answer
from commands.answer import answer
from commands.info import info

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
    """Post-initialization hook to set bot commands and start scheduler if enabled."""

    if application.bot_data["config"]['Features']['FSQuizScheduledSends']:
        setup_scheduler(application)
        logging.info("main/main - Scheduled quiz sends enabled.")

    commands = []

    # Conditional addition of mention handler command
    if application.bot_data["config"]['Features']['MentionHandler']:
        commands.append(BotCommand("tags", "List available tags"))

    # Conditional addition of ODG command
    if application.bot_data["config"]['Features']['ODGCommand']:
        commands.append(BotCommand("odg", "Show ODG"))

    # Conditional addition of Eagle API commands
    if application.bot_data["config"]['Features']['EAgleAPIIntegration']:
        commands.extend([
            BotCommand("inlab", "People currently in lab"),
            BotCommand("ore", "Your month's lab hours"),
        ])

    # Conditional addition of QR code generator command
    if application.bot_data["config"]['Features']['QRcodeGenerator']:
        commands.append(BotCommand("qr", "Generate a shlink QR code"))

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

    # Validate environment variables
    required_vars = ["TELEGRAM_BOT_TOKEN", "NOCO_API_KEY", "SHLINK_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        if "TELEGRAM_BOT_TOKEN" in missing_vars:
            logging.error("main/main - TELEGRAM_BOT_TOKEN environment variable is required but not set.")
            exit(1)
        if "NOCO_API_KEY" in missing_vars and config['Features']['NocoDBIntegration']:
            logging.error("main/main - NOCO_API_KEY environment variable is required but not set.")
            exit(1)
        if "SHLINK_API_KEY" in missing_vars and config['Features']['QRcodeGenerator']:
            logging.error("main/main - SHLINK_API_KEY environment variable is required but not set.")
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
    logging.getLogger("apscheduler").setLevel(logging.WARNING)

    application = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .post_init(ps)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    logging.info("main/main - T.E.C.S. started")

    # Store config in bot_data for global access
    application.bot_data["config"] = config

    # Initialize NocoDB client if enabled
    if config['Features']['NocoDBIntegration']:
        nocodb = NocoDB(config['Settings']['NOCO_URL'], os.getenv("NOCO_API_KEY"))
        application.bot_data["nocodb"] = nocodb
        logging.info("main/main - NocoDB integration enabled.")

    # Register handlers
    application.add_handler(CommandHandler("start", start))

    # Conditional registration of mention handler and /tags command
    if config['Features']['MentionHandler'] and config['Features']['NocoDBIntegration']:
        tag_cache = {
            "areas": nocodb.tags('area'),
            "workgroups": nocodb.tags('workgroup'),
            "projects": nocodb.tags('project'),
            "roles": nocodb.tags('role'),
        }
        application.bot_data["tag_cache"] = tag_cache
        application.add_handler(CommandHandler("tags", tags))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, mention_handler))
        logging.info("main/main - Mention handler and /tags command enabled and handlers registered.")

    if config['Features']['Whitelist'] and config['Features']['NocoDBIntegration'] and config['Features']['MentionHandler']:
        wh = Whitelist(tag_cache, nocodb)
        application.bot_data["whitelist"] = wh
        logging.info("main/main - Whitelist feature enabled.")

    # Conditional registration of info command
    if config['Features']['InfoCommand'] and config['Features']['Whitelist']:
        application.add_handler(CommandHandler("info", info))
        logging.info("main/main - Info command enabled and handler registered.")

    # Conditional registration of ODG command
    if config['Features']['ODGCommand']:
        application.add_handler(CommandHandler("odg", odg))
        logging.info("main/main - ODG command enabled and handler registered.")

    # Conditional registration of Eagle API handlers
    if config['Features']['EAgleAPIIntegration']:
        eagle_api = EagleAPI(config['Settings']['EAGLE_API_URL'])
        application.bot_data["eagle_api"] = eagle_api
        application.add_handler(CommandHandler("inlab", inlab))
        application.add_handler(CommandHandler("ore", ore))
        logging.info("main/main - Eagle API integration enabled and handlers registered.")

    # Conditional registration of QR code generator handler
    if config['Features']['QRcodeGenerator'] and config['Features']['Whitelist']:
        shlink_api = ShlinkAPI(config['Settings']['SHLINK_API_URL'], os.getenv("SHLINK_API_KEY"))
        application.bot_data["shlink_api"] = shlink_api
        application.add_handler(CommandHandler("qr", qr))
        logging.info("main/main - QR code generator feature enabled and handler registered.")

    # Conditional registration of quiz-related handlers
    if config['Features']['FSQuiz']:
        application.add_handler(CommandHandler("question", question))
        logging.info("main/main - Quiz feature enabled and handler registered.")

    if config['Features']['FSQuiz'] and config['Features']['Whitelist']:
        application.add_handler(CommandHandler("quiz", quiz))
        application.add_handler(CommandHandler("quizzes", quizzes))
        application.add_handler(CommandHandler("event", event))
        application.add_handler(CommandHandler("events", events))
        application.add_handler(CommandHandler("answer", answer))
        logging.info("main/main - Quiz admin features enabled and handlers registered.")

    if config['Features']['FSQuizLogging'] and config['Features']['FSQuiz'] and config['Features']['NocoDBIntegration']:
        application.add_handler(PollAnswerHandler(question_answer))
        logging.info("main/main - Quiz logging enabled and handlers registered.")

    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    logging.info("main/main - T.E.C.S. ended")
