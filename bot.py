import logging

from telegram import Update
from telegram.ext import ApplicationBuilder

import config
import db
from handlers import start, product, myorders, admin
from jobs import poller
from payments import klikqris


def main():
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
        level=logging.INFO,
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)

    db.init_db(config.DB_PATH)
    logger.info("Database siap: %s", config.DB_PATH)
    logger.info("Bot: @%s | Admin: %s", config.SHOP_NAME, config.ADMIN_USER_ID)

    # KlikQRIS payment gateway (opsional)
    if config.KLIKQRIS_ACTIVE:
        klikqris.init(
            api_key=config.KLIKQRIS_API_KEY,
            merchant_id=config.KLIKQRIS_MERCHANT_ID,
            mode=config.KLIKQRIS_MODE,
        )
        logger.info("KlikQRIS: aktif (mode %s)", config.KLIKQRIS_MODE)
    else:
        logger.warning(
            "KlikQRIS: non-aktif. Order akan pakai info transfer manual. "
            "Set KLIKQRIS_API_KEY & KLIKQRIS_MERCHANT_ID di .env untuk mengaktifkan."
        )

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    start.register(app)
    product.register(app)
    myorders.register(app)
    admin.register(app)

    # Background poller: auto-verify pembayaran QRIS
    if config.KLIKQRIS_ACTIVE and app.job_queue is not None:
        app.job_queue.run_repeating(
            poller.check_payments,
            interval=poller.POLL_INTERVAL,
            first=poller.POLL_INTERVAL,
            name="klikqris_poller",
        )
        logger.info("QRIS poller aktif (interval %ds)", poller.POLL_INTERVAL)

    logger.info("Bot mulai polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

    # Cleanup saat shutdown
    if config.KLIKQRIS_ACTIVE:
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(klikqris.shutdown())
        except Exception:
            pass


if __name__ == "__main__":
    main()
