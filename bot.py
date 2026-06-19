import logging
from telegram import Update
from telegram.ext import ApplicationBuilder
import config
import db
from handlers import start, product, myorders, admin


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

    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    start.register(app)
    product.register(app)
    myorders.register(app)
    admin.register(app)

    logger.info("Bot mulai polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
