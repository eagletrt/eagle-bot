import os

CHAT_WHITELIST = [
    -1002000027693, # E-Agle Engineering
    -1002785167462 # Pesa Debug
]

BOT_TOKEN: str = os.getenv("BOT_TOKEN")
NOCODB_API_TOKEN: str = os.getenv("NOCODB_API_TOKEN")
DEBUG_MODE: bool = os.getenv("DEBUG_MODE", "false") == "true"

if not BOT_TOKEN:
    raise EnvironmentError("BOT_TOKEN environment variable is not set")
if not NOCODB_API_TOKEN:
    raise EnvironmentError("NOCODB_API_TOKEN environment variable is not set")
