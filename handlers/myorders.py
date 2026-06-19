"""Handler /myorders — tampilkan daftar order milik user.

Spec: SPEC.md → Module Specs → handlers/myorders.py
- /myorders dan alias /pesanan
- Ambil order via db.get_user_orders(user_id)
- Jika kosong → "Belum ada orderan. Yuk order di /katalog."
- Jika ada → tampilkan 20 order terakhir dalam format Markdown.
"""
import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

import config  # noqa: F401  (diimpor sesuai konvensi modul lain)
import db
from .product import format_rupiah

logger = logging.getLogger(__name__)

# Pemetaan status order → emoji (sesuai spec)
_STATUS_EMOJI: dict[str, str] = {
    "pending": "⏳",
    "paid": "✅",
    "cancelled": "❌",
}


async def register(app) -> None:
    """Daftarkan CommandHandler untuk /myorders dan alias /pesanan."""
    app.add_handler(CommandHandler("myorders", cmd_myorders))
    app.add_handler(CommandHandler("pesanan", cmd_myorders))


async def cmd_myorders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Tampilkan 20 order terakhir milik user pemanggil."""
    try:
        user_id = update.effective_user.id
        orders = db.get_user_orders(user_id)

        # Kosong → arahkan ke katalog
        if not orders:
            await update.message.reply_text(
                "Belum ada orderan. Yuk order di /katalog."
            )
            return

        # db.get_user_orders sudah ORDER BY created_at DESC,
        # jadi [:20] = 20 orderan paling baru.
        recent = orders[:20]

        lines: list[str] = [
            "📋 *Orderan kamu*",
            f"(Total: {len(orders)})",
            "",
        ]

        for o in recent:
            order_id = o.get("id", "")
            product_name = o.get("product_name", "")
            qty = o.get("quantity", 0)
            total = o.get("total", 0)
            status = o.get("status", "pending")
            created_at = o.get("created_at", "")

            emoji = _STATUS_EMOJI.get(status, "⏳")

            lines.append(f"#{order_id}")
            lines.append(f"{product_name} x{qty}")
            lines.append(
                f"Total: Rp {format_rupiah(total)} • "
                f"Status: {emoji} {status}"
            )
            lines.append(str(created_at))
            lines.append("")

        text = "\n".join(lines).rstrip()

        await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.exception("cmd_myorders error: %s", e)
        # Balas ramah hanya jika belum ada reply sebelumnya
        try:
            await update.effective_message.reply_text(
                "Maaf, ada masalah. Coba lagi."
            )
        except Exception:
            pass