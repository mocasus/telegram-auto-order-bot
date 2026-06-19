"""Admin command handlers for Simpel Order Bot.

Registered commands:
- /addproduct  — ConversationHandler to add a new product
                  (NAME -> PRICE -> DESCRIPTION)
- /listproducts — list every product in the database
- /delproduct   — delete a product by id
- /orders       — list the most recent orders with inline status buttons
- /broadcast    — broadcast a message to every known user

Also registers a ``CallbackQueryHandler`` for the
``setstatus:<order_id>:<status>`` inline-button pattern emitted by ``/orders``
so the admin can mark orders as ``paid`` / ``cancelled`` / ``pending``.

All admin entry points first check
``update.effective_user.id == config.ADMIN_USER_ID`` and reply with
"⛔ Perintah ini khusus admin." otherwise.
"""

import logging

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

# ConversationHandler states for /addproduct.
NAME, PRICE, DESCRIPTION = 0, 1, 2

# Map order status -> emoji used in the /orders list.
_STATUS_EMOJI = {
    "pending": "⏳",
    "paid": "✅",
    "cancelled": "❌",
}


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _is_admin(update: Update) -> bool:
    """Return True when the effective user matches the configured admin."""
    user = update.effective_user
    return user is not None and user.id == config.ADMIN_USER_ID


async def _deny_non_admin(update: Update) -> None:
    """Reply to the effective chat with the standard 'admin only' message."""
    message = update.effective_message
    if message is None:
        return
    await message.reply_text("⛔ Perintah ini khusus admin.")


def format_rupiah(n: int) -> str:
    """Format an integer IDR amount as Indonesian-style ``50.000``."""
    return f"{n:,}".replace(",", ".")


# ---------------------------------------------------------------------------
# Handler registration
# ---------------------------------------------------------------------------


async def register(app: Application) -> None:
    """Register every admin handler on the supplied ``Application``."""

    conv_addproduct = ConversationHandler(
        entry_points=[CommandHandler("addproduct", addproduct_start)],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, addproduct_name
                )
            ],
            PRICE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, addproduct_price
                )
            ],
            DESCRIPTION: [
                # /skip must reach the description handler as a text
                # message, so we list it explicitly. /cancel intentionally
                # does NOT match here and is handled by the fallback
                # CommandHandler below.
                MessageHandler(
                    filters.Regex(r"^/skip$"), addproduct_description
                ),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, addproduct_description
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_addproduct)],
        per_message=False,
        per_chat=True,
        conversation_timeout=600,
    )

    app.add_handler(conv_addproduct)
    app.add_handler(CommandHandler("listproducts", cmd_listproducts))
    app.add_handler(CommandHandler("delproduct", cmd_delproduct))
    app.add_handler(CommandHandler("orders", cmd_orders))
    app.add_handler(
        CallbackQueryHandler(
            handle_setstatus,
            pattern=r"^setstatus:[A-Z0-9-]+:(paid|cancelled|pending)$",
        )
    )
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))


# ---------------------------------------------------------------------------
# /addproduct ConversationHandler
# ---------------------------------------------------------------------------


async def addproduct_start(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Entry point of ``/addproduct`` — reset state and ask for the name."""
    if not _is_admin(update):
        await _deny_non_admin(update)
        return -1

    message = update.effective_message
    if message is None:
        return -1

    context.user_data["new_product"] = {}
    await message.reply_text(
        "📝 *Tambah Produk Baru*\nKirim nama produk:",
        parse_mode=ParseMode.MARKDOWN,
    )
    return NAME


async def addproduct_name(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Store the product name and ask for the price."""
    message = update.effective_message
    if message is None or message.text is None:
        # Stay in the NAME state; the user can retype.
        return NAME

    context.user_data["new_product"]["name"] = message.text.strip()
    await message.reply_text(
        "Kirim harga (angka, contoh: `50000`):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return PRICE


async def addproduct_price(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Validate the entered price and ask for the description."""
    message = update.effective_message
    if message is None or message.text is None:
        return PRICE

    raw = message.text.strip().replace(".", "").replace(",", "")
    try:
        price = int(raw)
    except ValueError:
        await message.reply_text(
            "Harga tidak valid. Kirim angka saja. /cancel untuk batal."
        )
        return PRICE

    if price <= 0:
        await message.reply_text(
            "Harga tidak valid. Kirim angka saja. /cancel untuk batal."
        )
        return PRICE

    context.user_data["new_product"]["price"] = price
    await message.reply_text(
        "Kirim deskripsi (atau /skip untuk kosong):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return DESCRIPTION


async def addproduct_description(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Persist the new product (or honour ``/skip``) and end the conversation."""
    message = update.effective_message
    if message is None or message.text is None:
        return DESCRIPTION

    text = message.text.strip()
    desc = "" if text == "/skip" else text

    pending = context.user_data.get("new_product", {})
    name = pending.get("name", "")
    price = pending.get("price", 0)

    try:
        pid = db.add_product(name, price, desc)
    except Exception as exc:
        logger.exception("Gagal add_product: %s", exc)
        await message.reply_text(
            "Maaf, ada masalah saat menyimpan produk. Coba lagi."
        )
        context.user_data.clear()
        return -1

    await message.reply_text(
        "✅ Produk ditambahkan!\n"
        f"ID: {pid}\n"
        f"Nama: {name}\n"
        f"Harga: Rp {format_rupiah(price)}\n"
        f"Deskripsi: {desc or '(kosong)'}",
        parse_mode=ParseMode.MARKDOWN,
    )
    context.user_data.clear()
    return -1


async def cancel_addproduct(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Fallback handler that aborts the ``/addproduct`` conversation."""
    message = update.effective_message
    if message is not None:
        await message.reply_text("Dibatalkan.")
    context.user_data.clear()
    return -1


# ---------------------------------------------------------------------------
# Simple admin commands
# ---------------------------------------------------------------------------


async def cmd_listproducts(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle ``/listproducts`` — print every product."""
    if not _is_admin(update):
        await _deny_non_admin(update)
        return

    message = update.effective_message
    if message is None:
        return

    try:
        products = db.list_products()
    except Exception as exc:
        logger.exception("Gagal list_products: %s", exc)
        await message.reply_text("Maaf, ada masalah. Coba lagi.")
        return

    if not products:
        await message.reply_text("Belum ada produk.")
        return

    lines = []
    for p in products:
        desc = p.get("description") or ""
        lines.append(
            f"#{p['id']} — {p['name']} — Rp {format_rupiah(p['price'])}\n"
            f"   {desc}"
        )
    await message.reply_text("\n\n".join(lines), parse_mode=ParseMode.MARKDOWN)


async def cmd_delproduct(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle ``/delproduct <id>`` — remove a product by id."""
    if not _is_admin(update):
        await _deny_non_admin(update)
        return

    message = update.effective_message
    if message is None:
        return

    args = context.args or []
    if not args:
        await message.reply_text(
            "Gunakan: `/delproduct <id>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        pid = int(args[0])
    except ValueError:
        await message.reply_text("ID harus angka.")
        return

    try:
        ok = db.delete_product(pid)
    except Exception as exc:
        logger.exception("Gagal delete_product(%s): %s", pid, exc)
        await message.reply_text("Maaf, ada masalah. Coba lagi.")
        return

    if ok:
        await message.reply_text(f"✅ Produk #{pid} dihapus.")
    else:
        await message.reply_text("Produk tidak ditemukan.")


async def cmd_orders(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle ``/orders [status]`` — show the latest orders with buttons."""
    if not _is_admin(update):
        await _deny_non_admin(update)
        return

    message = update.effective_message
    if message is None:
        return

    # Optional status filter, e.g. ``/orders paid``.
    status_filter = context.args[0] if context.args else None

    try:
        orders = db.get_all_orders(limit=20, status=status_filter)
    except Exception as exc:
        logger.exception("Gagal get_all_orders: %s", exc)
        await message.reply_text("Maaf, ada masalah. Coba lagi.")
        return

    if not orders:
        await message.reply_text("Belum ada order.")
        return

    # Keep individual messages short: split into chunks of 10 orders.
    chunk_size = 10
    chunks = [
        orders[i : i + chunk_size] for i in range(0, len(orders), chunk_size)
    ]
    total = len(orders)

    for chunk in chunks:
        lines = [f"📦 *Order Terbaru* ({total})\n"]
        keyboard: list[list[InlineKeyboardButton]] = []

        for o in chunk:
            username = o.get("username") or "no_user"
            status = o.get("status", "pending")
            emoji = _STATUS_EMOJI.get(status, "⏳")
            order_id = o["id"]

            lines.append(
                f"#{order_id} | @{username}\n"
                f"Product #{o['product_id']} x{o['quantity']} = "
                f"Rp {format_rupiah(o['total'])}\n"
                f"Status: {emoji} {status}\n"
                f"{o.get('created_at', '')}\n"
            )
            keyboard.append(
                [
                    InlineKeyboardButton(
                        "✅ Paid",
                        callback_data=f"setstatus:{order_id}:paid",
                    ),
                    InlineKeyboardButton(
                        "❌ Cancel",
                        callback_data=f"setstatus:{order_id}:cancelled",
                    ),
                ]
            )

        await message.reply_text(
            "".join(lines),
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


# ---------------------------------------------------------------------------
# Inline-button callback: setstatus
# ---------------------------------------------------------------------------


async def handle_setstatus(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle the ``setstatus:<order_id>:<status>`` callback from ``/orders``."""
    query = update.callback_query
    if query is None:
        return

    # Always acknowledge the callback so the loading indicator disappears,
    # even if we are about to bail out.
    await query.answer()

    if not _is_admin(update):
        return

    try:
        _, order_id, new_status = query.data.split(":")
    except ValueError:
        logger.warning("Data setstatus tidak valid: %r", query.data)
        return

    try:
        db.update_order_status(order_id, new_status)
    except Exception as exc:
        logger.exception(
            "Gagal update_order_status(%s, %s): %s",
            order_id,
            new_status,
            exc,
        )
        try:
            await query.edit_message_text(
                "Maaf, ada masalah saat update status."
            )
        except Exception as inner_exc:  # pragma: no cover - defensive
            logger.warning("edit_message_text gagal: %s", inner_exc)
        return

    admin_id = update.effective_user.id if update.effective_user else "?"
    logger.info(
        "Order %s -> %s oleh admin %s", order_id, new_status, admin_id
    )

    try:
        await query.edit_message_text(
            f"✅ Status order #{order_id} diubah ke *{new_status}*.",
            parse_mode=ParseMode.MARKDOWN,
        )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("edit_message_text setstatus gagal: %s", exc)


# ---------------------------------------------------------------------------
# /broadcast
# ---------------------------------------------------------------------------


async def cmd_broadcast(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle ``/broadcast <message>`` — send the text to every known user."""
    if not _is_admin(update):
        await _deny_non_admin(update)
        return

    message = update.effective_message
    if message is None:
        return

    text = " ".join(context.args or []).strip()
    if not text:
        await message.reply_text(
            "Gunakan: `/broadcast <pesan>`", parse_mode=ParseMode.MARKDOWN
        )
        return

    try:
        user_ids = db.get_all_user_ids()
    except Exception as exc:
        logger.exception("Gagal get_all_user_ids: %s", exc)
        await message.reply_text("Maaf, ada masalah. Coba lagi.")
        return

    success = 0
    failed = 0
    for uid in user_ids:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=text,
                parse_mode=ParseMode.MARKDOWN,
            )
            success += 1
        except Exception as exc:
            logger.warning("Broadcast ke %s gagal: %s", uid, exc)
            failed += 1

    await message.reply_text(
        f"📣 Broadcast terkirim ke *{success}* user. Gagal: *{failed}*.",
        parse_mode=ParseMode.MARKDOWN,
    )
