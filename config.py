import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
AUTHORIZED_USER_ID = os.getenv("AUTHORIZED_USER_ID")

if not BOT_TOKEN:
    raise RuntimeError("Telegram bot token is missing")

if not AUTHORIZED_USER_ID:
    raise RuntimeError("Authorized Telegram user ID is missing")

try:
    AUTHORIZED_USER_ID = int(AUTHORIZED_USER_ID)
except ValueError:
    raise RuntimeError("Telegram user ID must be numeric")
