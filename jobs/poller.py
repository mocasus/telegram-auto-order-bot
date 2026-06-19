"""Background job: poll KlikQRIS status untuk semua order pending.

Dijadwalkan via JobQueue (lihat bot.py). Interval 10 detik.
Saat status berubah jadi 'paid' / 'expired', update DB dan kirim notifikasi
ke user (dan admin untuk order paid).
"""

from __future__ import annotations

import logging

from telegram.ext import ContextTypes

import config
import db
from payments import klikqris

logger = logging.getLogger(__name__)

POLL_INTERVAL = 10  # detik


async def check_payments(context: ContextTypes.DEFAULT_TYPE) -> None:
    """JobQueue callback: cek semua order QRIS yang masih pending."""
    if not klikqris.is_active():
        return

    try:
        orders = db.get_pending_qris_orders()
    except Exception as e:
        logger.exception("Gagal ambil pending orders: %s", e)
        return

    if not orders:
        return

    klik = klikqris.get()
    bot = context.bot

    for order in orders:
        order_id = order["id"]
        try:
            res = await klik.check_status(order_id)
            payment_status = (res.get("data") or {}).get("payment_status", "pending")
        except klikqris.KlikQRISError as e:
            logger.warning("Cek status %s gagal: %s", order_id, e)
            continue
        except Exception as e:
            logger.exception("Unexpected error cek %s: %s", order_id, e)
            continue

        if payment_status == "paid":
            db.update_order_status(order_id, "paid")
            logger.info("Order %s marked PAID via poller", order_id)
            # Notify user
            try:
                await bot.send_message(
                    chat_id=order["user_id"],
                    text=(
                        f"✅ Pembayaran diterima!\n\n"
                        f"Order *#{order_id}* sudah dibayar. "
                        f"Admin akan segera memproses pesanan kamu."
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Gagal notif user %s: %s", order["user_id"], e)
            # Notify admin
            try:
                await bot.send_message(
                    chat_id=config.ADMIN_USER_ID,
                    text=f"💰 Order *#{order_id}* sudah dibayar (auto-verify).",
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Gagal notif admin: %s", e)

        elif payment_status in ("expired", "failed", "cancelled"):
            db.update_order_status(order_id, "cancelled")
            logger.info("Order %s marked CANCELLED via poller (%s)", order_id, payment_status)
            try:
                await bot.send_message(
                    chat_id=order["user_id"],
                    text=(
                        f"⏰ Order *#{order_id}* kadaluarsa / dibatalkan "
                        f"(status: {payment_status}). Buat order baru di /katalog."
                    ),
                    parse_mode="Markdown",
                )
            except Exception as e:
                logger.warning("Gagal notif user %s: %s", order["user_id"], e)
