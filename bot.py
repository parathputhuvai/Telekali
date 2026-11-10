import logging
import time
from collections import defaultdict, deque

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, AUTHORIZED_USER_ID
from executor import execute_command


# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Prevent HTTP request URLs from exposing bot tokens
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Rate limiting configuration
COMMAND_LIMIT = 5
COMMAND_WINDOW = 60

command_history = defaultdict(deque)


def is_rate_limited(user_id):
    now = time.monotonic()
    history = command_history[user_id]

    while history and now - history[0] >= COMMAND_WINDOW:
        history.popleft()

    if len(history) >= COMMAND_LIMIT:
        return True

    history.append(now)
    return False


# Authentication
def is_authorized(update: Update) -> bool:
    user = update.effective_user

    return (
        user is not None
        and user.id == AUTHORIZED_USER_ID
    )


async def deny_access(update: Update):
    if update.effective_message:
        await update.effective_message.reply_text(
            "Access denied. You are not authorized."
        )


# /start
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await deny_access(update)
        return

    await update.effective_message.reply_text(
        "Welcome to TeleKali!\n\n"
        "Remote Kali Linux agent is connected.\n"
        "Use /help to see available commands."
    )


# /help
async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await deny_access(update)
        return

    help_text = (
        "TeleKali - Command Menu\n\n"

        "BASIC LINUX COMMANDS\n"
        "/cmd whoami\n"
        "/cmd uname -a\n"
        "/cmd ip a\n"
        "/cmd ip route\n"
        "/cmd df -h\n"
        "/cmd free -h\n\n"

        "NETWORK COMMANDS\n"
        "/cmd ping -c 2 192.168.100.5\n"
        "/cmd nmap 192.168.100.5\n"
        "/cmd nmap -F 192.168.100.5\n"
        "/cmd nmap -sV 192.168.100.5\n"
        "/cmd nmap -p 80,443 192.168.100.5\n"
        "/cmd nmap -sT -sV -p 80,443 192.168.100.5\n"
        "/cmd nmap --top-ports 100 192.168.100.5\n\n"

        "OTHER COMMANDS\n"
        "/start - Start bot\n"
        "/help - Show commands\n"
        "/status - Check status\n\n"

        "Only approved commands and authorized "
        "private IPv4 targets are accepted."
    )

    await update.effective_message.reply_text(help_text)


# /status
async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await deny_access(update)
        return

    await update.effective_message.reply_text(
        "TeleKali Status: ONLINE\n"
        "Telegram Connection: ACTIVE\n"
        "Authentication: VERIFIED"
    )


# /cmd
async def cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_authorized(update):
        await deny_access(update)
        return

    user_id = update.effective_user.id
    message = update.effective_message

    if is_rate_limited(user_id):
        await message.reply_text(
            "Rate limit exceeded.\n"
            "Maximum 5 command requests per minute."
        )
        return

    if not context.args:
        await message.reply_text(
            "Usage: /cmd <command>\n"
            "Example: /cmd whoami"
        )
        return

    command_text = " ".join(context.args)

    await message.reply_text("Executing command...")

    result = await execute_command(
        command_text,
        user_id,
    )

    # Telegram message length safety
    if len(result) > 4000:
        result = result[:4000] + "\n[Response truncated]"

    await message.reply_text(result)


# Main application
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing.")

    if not AUTHORIZED_USER_ID:
        raise ValueError("AUTHORIZED_USER_ID is missing.")

    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .build()
    )

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("help", help_command)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    application.add_handler(
        CommandHandler("cmd", cmd)
    )

    logger.info("Starting TeleKali...")

    application.run_polling()


if __name__ == "__main__":
    main()
