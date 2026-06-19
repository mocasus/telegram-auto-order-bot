"""Catalog & order conversation handlers for Simpel Order Bot.

Registered:
- /katalog — list products as inline-keyboard buttons.
- ConversationHandler that walks the user through:
    1. QTY      — ask for and validate the desired quantity.
    2. CONFIRM  — show payment info + Confirm/Cancel buttons.
  Entry point: any `order:<id>` callback from the catalog.
  Fallback:    /cancel at any time.

All replies use Markdown (legacy) parse mode so *bold*, _italic_, and
`code` work without escaping punctuation.
"""

from __future__ import annotations

import logging
import secrets
from datetime import datetime

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import config
import db

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Conversation states
# ---------------------------------------------------------------------------

QTY = 0
CONFIRM = 1


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def format_rupiah(n: int) -> str:
    """Format an integer as Indonesian Rupiah with dot separators.

    Example: 50000 -> "50.000".
    """
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


async def register(app: Application) -> None:
    """Register the /katalog command and the order ConversationHandler."""
    app.add_handler(CommandHandler("katalog", cmd_katalog))

    conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(ask_quantity, pattern=r"^order:\d+$"),
        ],
        states={
            QTY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_quantity,
                ),
            ],
            CONFIRM: [
                CallbackQueryHandler(
                    handle_confirm,
                    pattern=r"^confirm:(yes|no)$",
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_conversation),
        ],
        per_message=False,
        per_chat=True,
        conversation_timeout=600,
    )
    app.add_handler(conv_handler)


# ---------------------------------------------------------------------------
# /katalog
# ---------------------------------------------------------------------------


async def cmd_katalog(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """List products with one inline-keyboard button per product."""
    message = update.message
    if message is None:
        return

    try:
        products = db.list_products()
    except Exception as exc:
        logger.exception("Gagal mengambil daftar produk: %s", exc)
        await message.reply_text(
            "Maaf, ada masalah saat memuat katalog. Coba lagi sebentar.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    if not products:
        await message.reply_text(
            "Belum ada produk. Tanyakan admin untuk menambahkan.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    buttons: list[list[InlineKeyboardButton]] = []
    for product in products:
        label = f"🛒 {product['name']} - Rp {format_rupiah(product['price'])}"
        buttons.append(
            [InlineKeyboardButton(label, callback_data=f"order:{product['id']}")]
        )
    keyboard = InlineKeyboardMarkup(buttons)

    text = f"🛍️ *Katalog {config.SHOP_NAME}*"
    await message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard,
    )


# ---------------------------------------------------------------------------
# Conversation: entry point -> ask for quantity
# ---------------------------------------------------------------------------


async def ask_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Entry point: user clicked an `order:<id>` catalog button."""
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    try:
        pid = int(query.data.split(":")[1])
    except (IndexError, ValueError):
        await query.edit_message_text("Produk tidak ditemukan.")
        return ConversationHandler.END

    try:
        product = db.get_product(pid)
    except Exception as exc:
        logger.exception("Gagal mengambil produk %s: %s", pid, exc)
        await query.edit_message_text("Maaf, ada masalah. Coba lagi.")
        return ConversationHandler.END

    if product is None:
        await query.edit_message_text("Produk tidak ditemukan.")
        return ConversationHandler.END

    context.user_data["pending"] = {"product": product}

    await query.edit_message_text(
        f"Mau pesan berapa *{product['name']}*? (contoh: `2`)",
        parse_mode=ParseMode.MARKDOWN,
    )
    return QTY


# ---------------------------------------------------------------------------
# Conversation: QTY state -> validate quantity, show payment info
# ---------------------------------------------------------------------------


async def receive_quantity(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """QTY state: parse the typed quantity and ask for confirmation."""
    message = update.message
    if message is None or message.text is None:
        return QTY

    text = message.text.strip()
    try:
        qty = int(text)
    except ValueError:
        await message.reply_text(
            "Jumlah tidak valid. Masukkan angka >= 1. /cancel untuk batal.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return QTY

    if qty < 1:
        await message.reply_text(
            "Jumlah tidak valid. Masukkan angka >= 1. /cancel untuk batal.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return QTY

    pending = context.user_data.get("pending") or {}
    product = pending.get("product")
    if product is None:
        # Defensive: conversation state got out of sync.
        context.user_data.clear()
        await message.reply_text(
            "Sesi order sudah berakhir. Silakan mulai lagi dari /katalog.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    total = product["price"] * qty
    pending["quantity"] = qty
    pending["total"] = total
    context.user_data["pending"] = pending

    confirm_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Konfirmasi", callback_data="confirm:yes"),
                InlineKeyboardButton("❌ Batal", callback_data="confirm:no"),
            ]
        ]
    )

    text = (
        "📦 *Pesanan kamu*\n"
        f"Produk: {product['name']}\n"
        f"Jumlah: {qty}\n"
        f"Total: Rp {format_rupiah(total)}\n"
        "\n"
        f"💳 Pembayaran ke *{config.PAYMENT_BANK}* "
        f"`{config.PAYMENT_NUMBER}` a.n. *{config.PAYMENT_NAME}*\n"
        "\n"
        "Klik konfirmasi setelah transfer (atau siapkan bukti transfer dulu)."
    )

    await message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=confirm_keyboard,
    )
    return CONFIRM


# ---------------------------------------------------------------------------
# Conversation: CONFIRM state -> create or cancel the order
# ---------------------------------------------------------------------------


async def handle_confirm(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """CONFIRM state: persist the order on `confirm:yes`, abort on `confirm:no`."""
    query = update.callback_query
    if query is None:
        return ConversationHandler.END

    await query.answer()

    choice = query.data.split(":")[1] if query.data else ""

    if choice == "no":
        context.user_data.clear()
        await query.edit_message_text("❌ Dibatalkan.")
        return ConversationHandler.END

    # choice == "yes"
    pending = context.user_data.get("pending") or {}
    product = pending.get("product")
    if product is None or "quantity" not in pending or "total" not in pending:
        context.user_data.clear()
        await query.edit_message_text(
            "Sesi order sudah berakhir. Silakan mulai lagi dari /katalog.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    user = update.effective_user
    if user is None:
        context.user_data.clear()
        await query.edit_message_text("Gagal membuat order: user tidak dikenal.")
        return ConversationHandler.END

    order_id = (
        f"ORD-{datetime.now().strftime('%Y%m%d')}-"
        f"{secrets.token_hex(2).upper()}"
    )

    try:
        db.create_order(
            order_id,
            user.id,
            user.username,
            user.first_name,
            product["id"],
            pending["quantity"],
            pending["total"],
        )
    except Exception as exc:
        logger.exception("Gagal membuat order: %s", exc)
        context.user_data.clear()
        await query.edit_message_text(
            "Maaf, gagal membuat order. Coba lagi dari /katalog.",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    text = (
        f"✅ Order *#{order_id}* dibuat!\n"
        "\n"
        f"Total: Rp {format_rupiah(pending['total'])}\n"
        f"Bayar ke *{config.PAYMENT_BANK}* "
        f"`{config.PAYMENT_NUMBER}` a.n. *{config.PAYMENT_NAME}*.\n"
        "Admin akan verifikasi setelah transfer. "
        "Cek status di /myorders."
    )
    context.user_data.clear()
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


# ---------------------------------------------------------------------------
# Conversation: fallback -> /cancel
# ---------------------------------------------------------------------------


async def cancel_conversation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Fallback: user typed /cancel — clear state and end the conversation."""
    context.user_data.clear()
    message = update.message
    if message is not None:
        await message.reply_text("Dibatalkan.", parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END