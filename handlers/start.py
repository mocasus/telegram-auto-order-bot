"""Start, help, and menu command handlers for Simpel Order Bot.

Registered commands:
- /start — upsert user and send welcome message (Indonesian).
- /menu  — alias of /start.
- /help  — send help text (Indonesian).

All replies use Markdown (legacy) parse mode so *bold*, _italic_,
and `code` work without escaping punctuation.
"""

import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

import config
import db

logger = logging.getLogger(__name__)


async def register(app: Application) -> None:
    """Register the /start, /help, and /menu command handlers on the app."""
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    # /menu is an alias for /start.
    app.add_handler(CommandHandler("menu", cmd_start))


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start and /menu: upsert the user, then send the welcome message."""
    user = update.effective_user
    message = update.message
    if user is None or message is None:
        # No associated user (e.g. channel post); nothing meaningful to do.
        return

    try:
        db.upsert_user(user.id, user.username, user.first_name)
    except Exception as exc:
        logger.exception("Gagal upsert user %s: %s", user.id, exc)
        # Don't abort the welcome; the user can still use the bot.

    first_name = user.first_name or "teman"

    text = (
        f"👋 Halo {first_name}!\n"
        "\n"
        f"Selamat datang di *{config.SHOP_NAME}*.\n"
        "Ketuk /katalog untuk lihat produk, /myorders untuk orderan kamu, "
        "atau /help untuk bantuan."
    )

    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help: send a short Indonesian help message."""
    message = update.message
    if message is None:
        return

    text = (
        "📖 *Bantuan*\n"
        "\n"
        "/katalog — Lihat & order produk\n"
        "/myorders — Lihat orderan kamu\n"
        "/start — Menu utama\n"
        "\n"
        "Pembayaran manual transfer ke info yang diberikan saat order."
    )

    await message.reply_text(text, parse_mode=ParseMode.MARKDOWN)
