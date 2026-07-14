import logging


COLORS = {
	"INFO": "\033[94m",
	"WARNING": "\033[33m",
	"ERROR": "\033[91m",
	"RESET": "\033[0m",
}


class ColorFormatter(logging.Formatter):
	"""Custom logging formatter to add colors based on log level."""

	def format(self, record: logging.LogRecord) -> str:
		"""Format log messages with colors based on severity level."""

		message = super().format(record)
		levelname = record.levelname
		color = COLORS.get(levelname, COLORS["RESET"])
		marker = f"[{levelname}]"
		start = message.find(marker)
		if start != -1:
			end = start + len(marker)
			message = message[:start] + f"{color}{marker}{COLORS['RESET']}" + message[end:]
		return message


def _to_level(level_name: str, fallback: int = logging.INFO) -> int:
	"""Convert a log level name to a logging constant."""

	return getattr(logging, str(level_name).upper(), fallback)


def configure_bootstrap_logging(level: int = logging.INFO) -> None:
	"""Set up console logging early so startup errors are visible."""

	console_handler = logging.StreamHandler()
	console_handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))
	logging.basicConfig(level=level, handlers=[console_handler], force=True)


def configure_logging(config: dict) -> None:
	"""Configure logging from config (console + file + noisy libs)."""

	log_level_console = _to_level(config["Settings"]["ConsoleLogLevel"], logging.INFO)
	log_level_file = _to_level(config["Settings"]["FileLogLevel"], logging.WARNING)
	log_file_path = config["Paths"]["LogFilePath"]

	configure_bootstrap_logging(log_level_console)

	root_logger = logging.getLogger()

	file_handler = logging.FileHandler(log_file_path, mode="a", encoding="utf-8")
	file_handler.setLevel(log_level_file)
	file_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
	root_logger.addHandler(file_handler)

	logging.getLogger("httpx").setLevel(logging.WARNING)
	logging.getLogger("telegram").setLevel(logging.WARNING)
	logging.getLogger("apscheduler").setLevel(logging.WARNING)
