import os

BOT_TOKEN: str = os.getenv("BOT_TOKEN")
NOCODB_API_TOKEN: str = os.getenv("NOCODB_API_TOKEN")

if not BOT_TOKEN:
    raise EnvironmentError("BOT_TOKEN environment variable is not set")
if not NOCODB_API_TOKEN:
    raise EnvironmentError("NOCODB_API_TOKEN environment variable is not set")
