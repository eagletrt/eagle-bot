import logging
import os
import re
import traceback
from html import escape
from pathlib import Path
from time import monotonic
from telegram.ext import Application

PROJECT_ROOT = Path(__file__).resolve().parents[1]

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
    console_handler.setLevel(level)
    console_handler.setFormatter(ColorFormatter("%(asctime)s [%(levelname)s] %(message)s"))
    logging.basicConfig(level=logging.NOTSET, handlers=[console_handler], force=True)

class TelegramLogHandler(logging.Handler):
    """Send matching log records to a Telegram group/thread."""

    MAX_MESSAGE_LENGTH = 3500
    DUPLICATE_WINDOW_SECONDS = 60
    SENSITIVE_PATTERNS = (
        r"(?i)(token|password|api[_-]?key|secret)\s*[:=]\s*[^\s,;]+",
        r"(?i)(bearer\s+)[A-Za-z0-9._\-+/=]+",
    )

    def __init__(self, application: Application, chat_id: str, thread_id: str | None) -> None:
        super().__init__()
        self.application = application
        self.chat_id = chat_id
        self.thread_id = thread_id
        self._recent_messages: dict[str, float] = {}

    def _sanitize_message(self, message: str) -> str:
        """Redact common secrets and trim oversized payloads."""

        for env_name in ("TELEGRAM_BOT_TOKEN", "DB_PASSWORD", "SHLINK_API_KEY"):
            secret_value = os.getenv(env_name)
            if secret_value:
                message = message.replace(secret_value, f"[REDACTED:{env_name}]")

        for pattern in self.SENSITIVE_PATTERNS:
            message = re.sub(pattern, lambda match: f"{match.group(1)}[REDACTED]", message)

        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = f"{message[: self.MAX_MESSAGE_LENGTH]}\n...[truncated]"

        return message

    def _prune_recent_messages(self, now: float) -> None:
        """Remove duplicate-tracking entries outside the suppression window."""

        cutoff = now - self.DUPLICATE_WINDOW_SECONDS
        self._recent_messages = {
            message: timestamp
            for message, timestamp in self._recent_messages.items()
            if timestamp >= cutoff
        }

    def _should_suppress_duplicate(self, message: str) -> bool:
        """Drop repeated messages in a short time window."""

        now = monotonic()
        self._prune_recent_messages(now)
        last_seen = self._recent_messages.get(message)
        self._recent_messages[message] = now
        return last_seen is not None and now - last_seen < self.DUPLICATE_WINDOW_SECONDS

    async def _send_message(self, message: str) -> None:
        await self.application.bot.send_message(
            chat_id=self.chat_id,
            message_thread_id=self.thread_id,
            parse_mode="HTML",
            text=message,
        )

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            message = self._sanitize_message(message)
            if self._should_suppress_duplicate(message):
                return
            self.application.create_task(self._send_message(message))
        except Exception:
            self.handleError(record)


class TelegramFormatter(logging.Formatter):
    """Format log records as a readable HTML message for Telegram."""

    def _relative_path(self, pathname: str) -> str:
        """Render paths relative to the repository root when possible."""

        resolved_path = Path(pathname).resolve()
        if resolved_path.is_relative_to(PROJECT_ROOT):
            return str(resolved_path.relative_to(PROJECT_ROOT))
        return os.path.relpath(resolved_path, start=PROJECT_ROOT)

    def formatException(self, ei) -> str:
        """Render traceback frames with relative paths and no redundant header."""

        traceback_exception = traceback.TracebackException.from_exception(ei[1], capture_locals=False)
        lines = []
        for frame in traceback_exception.stack:
            relative_path = escape(self._relative_path(frame.filename))
            lines.append(f'  File "{relative_path}", line {frame.lineno}, in {escape(frame.name)}')
            if frame.line:
                lines.append(f"    {escape(frame.line.strip())}")

        lines.extend(escape(line) for line in traceback_exception.format_exception_only())
        return "\n".join(lines)

    def format(self, record: logging.LogRecord) -> str:
        message = escape(record.getMessage())
        source_path = escape(self._relative_path(record.pathname))
        function_name = escape(record.funcName)
        lines = [
            f"<b>Severity:</b> {escape(record.levelname)}",
            f"<b>Time:</b> {escape(self.formatTime(record, '%Y-%m-%d %H:%M:%S'))}",
            f"<b>Source:</b> {source_path}:{record.lineno} in {function_name}",
            f"<b>Message:</b> {message}",
        ]

        if record.exc_info:
            lines.append("<b>Traceback:</b>")
            lines.append(self.formatException(record.exc_info))

        return "\n\n".join(lines)


def configure_logger_reporting(config: dict, application: Application) -> None:
    """Configure logging to report matching records to a Telegram group/thread."""

    report_level = _to_level(config["Settings"]["ReportLogLevel"], logging.ERROR)
    report_handler = TelegramLogHandler(
        application,
        config["Settings"]["ReportGroupID"],
        config["Settings"]["ReportThreadID"],
    )
    report_handler.setLevel(report_level)
    report_handler.setFormatter(TelegramFormatter())
    logging.getLogger().addHandler(report_handler)

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
