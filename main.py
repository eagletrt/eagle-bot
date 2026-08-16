import os
import logging
import sys
import tomllib
from dataclasses import dataclass
from typing import Callable
from modules.database import DatabaseClient
from modules.inlab import InLabClient
from modules.logger import configure_bootstrap_logging, configure_logging, configure_logger_reporting
from modules.shlink import ShlinkAPI
from modules.whitelist import Whitelist
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from modules.scheduler import setup_scheduler

# Import command handlers
from commands.start import start
from commands.odg import odg
from commands.shop import shop
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
from commands.answer import answer
from commands.id import id
from commands.no import no
from commands.eduardo import eduardo


@dataclass(frozen=True)
class CommandSpec:
    """Describes a slash command and when it should be enabled."""

    name: str
    description: str
    handler: Callable
    enabled: Callable[[dict], bool]
    publish: bool = True


COMMAND_SPECS = [
    CommandSpec("start", "Show a welcome message", start, lambda config: True, publish=False),
    CommandSpec("no", "Show a random excuse", no, lambda config: config["Features"]["Memes"], publish=False),
    CommandSpec("eduardo", "Send an animation of Eduardo", eduardo, lambda config: config["Features"]["Memes"], publish=False),
    CommandSpec(
        "tags",
        "List available tags",
        tags,
        lambda config: config["Features"]["MentionHandler"] and config["Features"]["DatabaseIntegration"] and config["Features"]["Whitelist"],
    ),
    CommandSpec("id", "Show the current chat ID and your user ID", id, lambda config: config["Features"]["IDCommand"], publish=False),
    CommandSpec("odg", "Show ODG", odg, lambda config: config["Features"]["ODGCommand"]),
    CommandSpec("shop", "Show shop items", shop, lambda config: config["Features"]["ShopCommand"]),
    CommandSpec(
        "inlab",
        "People currently in lab",
        inlab,
        lambda config: config["Features"]["InLabIntegration"] and config["Features"]["DatabaseIntegration"],
    ),
    CommandSpec(
        "ore",
        "Your month's lab hours",
        ore,
        lambda config: config["Features"]["InLabIntegration"] and config["Features"]["DatabaseIntegration"],
    ),
    CommandSpec("qr", "Generate a shlink QR code", qr, lambda config: config["Features"]["QRcodeGenerator"]),
    CommandSpec("question", "Get a random question", question, lambda config: config["Features"]["FSQuiz"]),
    CommandSpec("quiz", "Fetch details for a quiz", quiz, lambda config: config["Features"]["FSQuiz"], publish=False),
    CommandSpec("quizzes", "List available quizzes", quizzes, lambda config: config["Features"]["FSQuiz"], publish=False),
    CommandSpec("event", "Show a random event", event, lambda config: config["Features"]["FSQuiz"], publish=False),
    CommandSpec("events", "Show upcoming events", events, lambda config: config["Features"]["FSQuiz"], publish=False),
    CommandSpec("answer", "Answer an open-ended question", answer, lambda config: config["Features"]["FSQuiz"], publish=False),
]


def load_config(config_path: str) -> dict:
    """Load the TOML configuration file."""

    try:
        with open(config_path, "rb") as config_file:
            return tomllib.load(config_file)
    except FileNotFoundError:
        logging.error("main/main - CONFIG_PATH points to a file that does not exist: %s", config_path)
        sys.exit(1)
    except tomllib.TOMLDecodeError as error:
        logging.error("main/main - Error parsing config file %s: %s", config_path, error)
        sys.exit(1)


def validate_environment(config: dict) -> None:
    """Validate environment variables required by the enabled features."""

    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        logging.error("main/main - TELEGRAM_BOT_TOKEN environment variable is required but not set.")
        sys.exit(1)

    if config["Features"]["QRcodeGenerator"] and not os.getenv("SHLINK_API_KEY"):
        logging.error("main/main - SHLINK_API_KEY environment variable is required but not set.")
        sys.exit(1)

    db_features_enabled = any(
        config["Features"][feature]
        for feature in ["ODGCommand", "FSQuiz", "DatabaseIntegration", "InLabIntegration", "MentionHandler", "Whitelist", "ShopCommand"]
    )
    if db_features_enabled and not os.getenv("DB_PASSWORD"):
        logging.error("main/main - DB_PASSWORD environment variable is required but not set.")
        sys.exit(1)


def enabled_command_specs(config: dict) -> list[CommandSpec]:
    """Return the commands enabled by the current configuration."""

    return [spec for spec in COMMAND_SPECS if spec.enabled(config)]


def register_feature_handlers(application: Application, config: dict) -> None:
    """Register command handlers based on the active feature set."""

    for spec in enabled_command_specs(config):
        application.add_handler(CommandHandler(spec.name, spec.handler))
        logging.info("main/main - Registered /%s handler.", spec.name)

    if config["Features"]["MentionHandler"] and config["Features"]["DatabaseIntegration"] and config["Features"]["Whitelist"]:
        application.add_handler(MessageHandler((filters.TEXT | filters.CAPTION) & ~filters.COMMAND, mention_handler))
        logging.info("main/main - Mention handler registered.")


def initialize_runtime_services(application: Application, config: dict) -> None:
    """Initialize clients and caches that handlers depend on."""

    if config["Features"]["DatabaseIntegration"]:
        database = DatabaseClient(application)
        application.bot_data["database"] = database
        logging.info("main/main - Database integration enabled.")

    if config["Features"]["InLabIntegration"] and config["Features"]["DatabaseIntegration"]:
        inlab_client = InLabClient(application)
        application.bot_data["inlabClient"] = inlab_client
        logging.info("main/main - InLab integration enabled.")

    if config["Features"]["QRcodeGenerator"]:
        shlink_api = ShlinkAPI(config["Settings"]["SHLINK_API_URL"], os.getenv("SHLINK_API_KEY"))
        application.bot_data["shlink_api"] = shlink_api
        logging.info("main/main - QR code generator feature enabled.")

    if config["Features"]["FSQuiz"]:
        application.bot_data["areas"] = config["Settings"]["areas"]
        logging.info("main/main - Quiz feature enabled.")

    if config["Features"]["Logger"]:
        configure_logger_reporting(config, application)
        logging.info("main/main - Logger reporting feature enabled.")

configure_bootstrap_logging()

async def ps(application: Application) -> None:
    """Post-initialization hook to set bot commands and start scheduler if enabled."""

    if application.bot_data["config"]['Features']['DatabaseIntegration']:
        # Initialize tag cache
        application.bot_data["tag_cache"] = await application.bot_data['database'].load_tag_cache()
        logging.info("main/main - Tag cache initialized.")

    if application.bot_data["config"]['Features']['FSQuizScheduledSends']:
        setup_scheduler(application)
        logging.info("main/main - Scheduled quiz sends enabled.")

    if application.bot_data["config"]['Features']['Whitelist'] and application.bot_data["config"]['Features']['DatabaseIntegration'] and application.bot_data["config"]['Features']['MentionHandler']:
        application.bot_data["whitelist"] = Whitelist(application)
        logging.info("main/main - Whitelist feature enabled.")

    commands = [BotCommand(spec.name, spec.description) for spec in enabled_command_specs(application.bot_data["config"]) if spec.publish]
    await application.bot.set_my_commands(commands)
    logging.info("main/main - Bot commands published.")

def main() -> None:
    """Main function to set up and run the bot."""

    config_path = os.getenv("CONFIG_PATH")
    if not config_path:
        logging.error("main/main - CONFIG_PATH environment variable is required but not set.")
        sys.exit(1)

    config = load_config(config_path)
    validate_environment(config)

    configure_logging(config)

    application = (
        Application.builder()
        .token(os.getenv("TELEGRAM_BOT_TOKEN"))
        .post_init(ps)
        .read_timeout(30)
        .write_timeout(30)
        .build()
    )

    logging.info("main/main - TECS started")

    # Store config in bot_data for global access
    application.bot_data["config"] = config

    initialize_runtime_services(application, config)
    register_feature_handlers(application, config)

    # Start polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
    logging.info("main/main - TECS ended")
