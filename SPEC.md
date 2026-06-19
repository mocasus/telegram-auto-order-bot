# Simpel Order Bot — Specification v1.0

## Goal
Mengganti bot lama (terlalu kompleks) dengan bot Telegram yang **simpel dan mudah dipakai**. Alur: pilih produk → order → dapat info pembayaran → konfirmasi. Admin kelola produk & order.

## Tech Stack
- Python 3.11
- python-telegram-bot v22.x (async)
- SQLite (stdlib `sqlite3`, `check_same_thread=False`)
- python-dotenv
- **Tidak ada**: ORM, payment gateway otomatis, webhook, keranjang, kategori, multi-admin.

## File Structure
```
telegram-auto-order-bot/
├── bot.py              # Entry point
├── config.py           # Load .env & constants
├── db.py               # SQLite init + helpers
├── handlers/
│   ├── __init__.py     # Re-export submodules
│   ├── start.py        # /start, /help, /menu
│   ├── product.py      # /katalog + order ConversationHandler
│   ├── myorders.py     # /myorders
│   └── admin.py        # /addproduct, /listproducts, /delproduct, /orders, /broadcast
├── .env
├── requirements.txt
├── README.md
└── SPEC.md
```

## Environment Variables (.env)
| Var | Required | Default | Keterangan |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Token dari @BotFather |
| `ADMIN_USER_ID` | ✅ | — | Telegram user ID admin (int) |
| `PAYMENT_BANK` | ❌ | `BCA` | Nama bank/e-wallet |
| `PAYMENT_NUMBER` | ❌ | `123-456-789` | Nomor rekening |
| `PAYMENT_NAME` | ❌ | `Moca` | Atas nama |
| `SHOP_NAME` | ❌ | `Toko Moca` | Nama toko |
| `DB_PATH` | ❌ | `data/bot.db` | Path SQLite |

## Database Schema
```sql
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  price INTEGER NOT NULL,           -- IDR, tanpa desimal
  description TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,              -- "ORD-20260119-A3B2"
  user_id INTEGER NOT NULL,
  username TEXT,
  first_name TEXT,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  total INTEGER NOT NULL,
  status TEXT DEFAULT 'pending',    -- pending | paid | cancelled
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  last_seen TEXT DEFAULT (datetime('now'))
);
```

---

## Module Specs

### `config.py`
Load `.env` pakai `python-dotenv`. Expose konstanta:
- `BOT_TOKEN: str`
- `ADMIN_USER_ID: int`
- `PAYMENT_BANK: str`
- `PAYMENT_NUMBER: str`
- `PAYMENT_NAME: str`
- `SHOP_NAME: str`
- `DB_PATH: str`

Behavior:
- `load_dotenv(dotenv_path=Path(__file__).parent / ".env")` di top-level.
- Jika `BOT_TOKEN` kosong → `raise SystemExit("TELEGRAM_BOT_TOKEN tidak ditemukan di .env")`.
- `ADMIN_USER_ID` di-cast `int`. Jika invalid → `raise SystemExit(...)`.
- Konstanta lain pakai `os.getenv(key, default)`.

### `db.py`
Module-level `_conn: sqlite3.Connection | None`.

Functions (semua `def` biasa, bukan async):
- `init_db(path: str) -> None`
  - `Path(path).parent.mkdir(parents=True, exist_ok=True)`
  - `sqlite3.connect(str(path), check_same_thread=False)`
  - Set `row_factory = sqlite3.Row`
  - `executescript()` untuk 3 tabel di atas.
  - `commit()`
- `_row_to_dict(row) -> dict` (helper internal)
- `add_product(name, price, description) -> int` (return lastrowid)
- `list_products() -> list[dict]`
- `get_product(pid: int) -> dict | None`
- `delete_product(pid: int) -> bool` (True kalau ada row berubah)
- `create_order(order_id, user_id, username, first_name, product_id, quantity, total) -> None`
- `get_user_orders(user_id: int) -> list[dict]` (urut `created_at DESC`)
- `get_all_orders(limit: int = 50, status: str | None = None) -> list[dict]`
- `update_order_status(order_id: str, status: str) -> bool`
- `upsert_user(user_id, username, first_name) -> None` (`INSERT OR REPLACE INTO users ...`, update `last_seen=datetime('now')`)
- `get_all_user_ids() -> list[int]`

Setiap return dict pakai `_row_to_dict`. Catch `sqlite3.Error` di level modul? **Tidak** — biarkan raise, handler tangkap.

### `handlers/__init__.py`
```python
from . import start, product, myorders, admin
```

### `handlers/start.py`
- `async def register(app: Application) -> None`
  - `app.add_handler(CommandHandler("start", cmd_start))`
  - `app.add_handler(CommandHandler("help", cmd_help))`
  - `app.add_handler(CommandHandler("menu", cmd_start))`
- `async def cmd_start(update, context)`
  - `db.upsert_user(update.effective_user.id, update.effective_user.username, update.effective_user.first_name)`
  - Balas:
    ```
    👋 Halo {first_name}!

    Selamat datang di *{SHOP_NAME}*.
    Ketuk /katalog untuk lihat produk, /myorders untuk orderan kamu, atau /help untuk bantuan.
    ```
- `async def cmd_help(update, context)`
  - Balas:
    ```
    📖 *Bantuan*

    /katalog — Lihat & order produk
    /myorders — Lihat orderan kamu
    /start — Menu utama

    Pembayaran manual transfer ke info yang diberikan saat order.
    ```

### `handlers/product.py`
- `async def register(app)`
  - `app.add_handler(CommandHandler("katalog", cmd_katalog))`
  - `app.add_handler(conv_handler)` (lihat bawah)

- `async def cmd_katalog(update, context)`
  - `products = db.list_products()`
  - Kosong → "Belum ada produk. Tanyakan admin untuk menambahkan."
  - Else: format list + inline keyboard:
    ```
    🛍️ *Katalog {SHOP_NAME}*
    ```
    Lalu per produk: tombol `🛒 {name} - Rp {price}` dengan callback_data `order:{id}`.
    Parse harga pakai `format_rupiah(price)` (format Indonesia, misal `50.000`).

- **ConversationHandler** untuk order:
  - States: `QTY = 0`, `CONFIRM = 1`
  - `entry_points=[CallbackQueryHandler(ask_quantity, pattern=r"^order:\d+$")]`
  - `states={
        QTY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_quantity)],
        CONFIRM: [CallbackQueryHandler(handle_confirm, pattern=r"^confirm:(yes|no)$")],
      }`
  - `fallbacks=[CommandHandler("cancel", cancel_conversation)]`
  - `per_message=False`, `per_chat=True`, `conversation_timeout=600` (10 menit)

- `async def ask_quantity(update, context)`
  - `await update.callback_query.answer()`
  - Parse pid dari `update.callback_query.data.split(":")[1]` (int)
  - `product = db.get_product(pid)`. Jika None → "Produk tidak ditemukan.", return `-1` (END).
  - Simpan di `context.user_data["pending"] = {"product": product}`
  - Kirim: "Mau pesan berapa *{name}*? (contoh: `2`)"
  - Return `QTY`

- `async def receive_quantity(update, context)`
  - `text = update.message.text.strip()`
  - Try `int(text)`. Kalau gagal atau `<1`:
    - Balas: "Jumlah tidak valid. Masukkan angka >= 1. /cancel untuk batal."
    - Return `QTY`
  - `qty = int(text)`
  - `product = context.user_data["pending"]["product"]`
  - `total = product["price"] * qty`
  - `context.user_data["pending"]["quantity"] = qty`
  - `context.user_data["pending"]["total"] = total`
  - Kirim:
    ```
    📦 *Pesanan kamu*
    Produk: {name}
    Jumlah: {qty}
    Total: Rp {format_rupiah(total)}

    💳 Pembayaran ke *{PAYMENT_BANK}* `{PAYMENT_NUMBER}` a.n. *{PAYMENT_NAME}*

    Klik konfirmasi setelah transfer (atau siapkan bukti transfer dulu).
    ```
    Inline: `[✅ Konfirmasi] [❌ Batal]` dengan callback `confirm:yes` / `confirm:no`.
  - Return `CONFIRM`

- `async def handle_confirm(update, context)`
  - `await update.callback_query.answer()`
  - `choice = update.callback_query.data.split(":")[1]`
  - Jika `no`:
    - Edit pesan: "❌ Dibatalkan."
    - `context.user_data.clear()`
    - Return `-1` (END)
  - Jika `yes`:
    - `pending = context.user_data.get("pending", {})`
    - `product = pending["product"]`
    - `user = update.effective_user`
    - `order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(2).upper()}"`
    - `db.create_order(order_id, user.id, user.username, user.first_name, product["id"], pending["quantity"], pending["total"])`
    - Edit pesan:
      ```
      ✅ Order *#{order_id}* dibuat!

      Total: Rp {format_rupiah(pending["total"])}
      Bayar ke *{PAYMENT_BANK}* `{PAYMENT_NUMBER}` a.n. *{PAYMENT_NAME}*.
      Admin akan verifikasi setelah transfer. Cek status di /myorders.
      ```
    - `context.user_data.clear()`
    - Return `-1` (END)

- `async def cancel_conversation(update, context)`
  - `context.user_data.clear()`
  - Balas: "Dibatalkan."
  - Return `-1` (END)

- Helper: `def format_rupiah(n: int) -> str`: format pakai `f"{n:,}".replace(",", ".")`.

### `handlers/myorders.py`
- `async def register(app)`
  - `app.add_handler(CommandHandler("myorders", cmd_myorders))`
  - `app.add_handler(CommandHandler("pesanan", cmd_myorders))`  # alias
- `async def cmd_myorders(update, context)`
  - `orders = db.get_user_orders(update.effective_user.id)`
  - Kosong → "Belum ada orderan. Yuk order di /katalog."
  - Else: format list (max 20 terakhir):
    ```
    📋 *Orderan kamu*
    (Total: {len(orders)})
    
    #{order_id}
    {product_name} x{qty}
    Total: Rp {total} • Status: {status_emoji} {status}
    {created_at}
    ```
    status_emoji: pending=⏳, paid=✅, cancelled=❌.

### `handlers/admin.py`
Semua command cek `if update.effective_user.id != config.ADMIN_USER_ID: await update.message.reply_text("⛔ Perintah ini khusus admin."); return`.

- `async def register(app)`
  - `app.add_handler(conv_addproduct)` (ConversationHandler)
  - `app.add_handler(CommandHandler("listproducts", cmd_listproducts))`
  - `app.add_handler(CommandHandler("delproduct", cmd_delproduct))`
  - `app.add_handler(CommandHandler("orders", cmd_orders))`
  - `app.add_handler(CallbackQueryHandler(handle_setstatus, pattern=r"^setstatus:[A-Z0-9-]+:(paid|cancelled|pending)$"))`
  - `app.add_handler(CommandHandler("broadcast", cmd_broadcast))`

- **ConversationHandler `/addproduct`**: states `NAME=0, PRICE=1, DESCRIPTION=2`
  - Entry: `CommandHandler("addproduct", addproduct_start)` (juga cek admin di dalam handler)
  - `async def addproduct_start(update, context)`:
    - Cek admin (jika bukan → "⛔ Khusus admin." return `-1`)
    - `context.user_data["new_product"] = {}`
    - Balas: "📝 *Tambah Produk Baru*\nKirim nama produk:"
    - Return `NAME`
  - `async def addproduct_name(update, context)`:
    - `context.user_data["new_product"]["name"] = update.message.text.strip()`
    - Balas: "Kirim harga (angka, contoh: `50000`):"
    - Return `PRICE`
  - `async def addproduct_price(update, context)`:
    - Try `int(update.message.text.strip().replace(".", "").replace(",", ""))`. Gagal atau `<=0`:
      - Balas: "Harga tidak valid. Kirim angka saja. /cancel untuk batal."
      - Return `PRICE`
    - `context.user_data["new_product"]["price"] = int(...)`
    - Balas: "Kirim deskripsi (atau /skip untuk kosong):"
    - Return `DESCRIPTION`
  - `async def addproduct_description(update, context)`:
    - `text = update.message.text.strip()`
    - `desc = "" if text == "/skip" else text`
    - `p = context.user_data["new_product"]`
    - `pid = db.add_product(p["name"], p["price"], desc)`
    - Balas:
      ```
      ✅ Produk ditambahkan!
      ID: {pid}
      Nama: {p["name"]}
      Harga: Rp {format_rupiah(p["price"])}
      Deskripsi: {desc or '(kosong)'}
      ```
    - `context.user_data.clear()`
    - Return `-1`
  - Fallback: `CommandHandler("cancel", cancel_addproduct)` → "Dibatalkan.", clear user_data, END.

- `async def cmd_listproducts(update, context)`
  - Cek admin.
  - `products = db.list_products()`
  - Kosong → "Belum ada produk."
  - Else: list per baris: `#{id} — {name} — Rp {format_rupiah(price)}\n   {description}`

- `async def cmd_delproduct(update, context)`
  - Cek admin.
  - `args = context.args`. Jika kosong → "Gunakan: `/delproduct <id>`".
  - Try `int(args[0])`. Gagal → "ID harus angka."
  - `db.delete_product(pid)`. Balas: "✅ Produk #{pid} dihapus." (atau "Produk tidak ditemukan.")

- `async def cmd_orders(update, context)`
  - Cek admin.
  - `orders = db.get_all_orders(limit=20)`. (Optional: filter status via `context.args[0]` misal `/orders paid`.)
  - Kosong → "Belum ada order."
  - Else: untuk setiap order, kirim pesan terpisah atau edit? **Pakai satu pesan** dengan format:
    ```
    📦 *Order Terbaru* ({len(orders)})
    
    #{id} | @{username or 'no_user'}
    Product #{pid} x{qty} = Rp {total}
    Status: {status_emoji} {status}
    {created_at}
    ```
    Lalu inline keyboard per order: `[✅ Paid] [❌ Cancel]` dengan callback `setstatus:{order_id}:paid` / `setstatus:{order_id}:cancelled`.
    *Catatan*: kalau order lebih dari 10, pecah jadi beberapa pesan agar tidak terlalu panjang.

- `async def handle_setstatus(update, context)`
  - Cek admin.
  - `await update.callback_query.answer()`
  - Parse: `order_id, new_status = update.callback_query.data.split(":")[1:]`
  - `db.update_order_status(order_id, new_status)`
  - Edit pesan: tambahkan line `~ Diubah jadi {new_status} oleh admin ~` di bawah order yang relevan. Atau edit keseluruhan message dengan list baru. **Simplest**: edit message text jadi: `✅ Status order #{order_id} diubah ke *{new_status}*.` (replace seluruh isi).
  - Log info.

- `async def cmd_broadcast(update, context)`
  - Cek admin.
  - `text = " ".join(context.args)`. Jika kosong → "Gunakan: `/broadcast <pesan>`".
  - `user_ids = db.get_all_user_ids()`
  - Loop, kirim pesan ke tiap user_id. Tangkap exception per user.
  - Balas admin: "📣 Broadcast terkirim ke *{success}* user. Gagal: *{failed}*."

### `bot.py`
```python
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
```

---

## Conventions
- Semua handler `async def`.
- Import: `from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup` etc. sesuai kebutuhan.
- Parse mode: pakai `ParseMode.MARKDOWN` di `reply_text` (via `update.message.reply_text(..., parse_mode=ParseMode.MARKDOWN)`) atau default Markdown V2? **Pakai Markdown V2** untuk button label? Tidak, label button bukan parsed. Pakai `parse_mode=ParseMode.MARKDOWN` di reply text biasa. Untuk karakter khusus: escape `.`, `!`, dll. **Saran**: pakai `parse_mode=ParseMode.MARKDOWN` (legacy) saja agar tidak perlu escape ribet. Bintang dan underscore aman. Backtick juga.
  - **Pilih**: `parse_mode=ParseMode.MARKDOWN` (Markdown legacy). Aman untuk `*bold*`, `_italic_`, `` `code` ``.
- Error handling: di setiap handler, `try/except Exception as e: logger.exception(e); await update.effective_message.reply_text("Maaf, ada masalah. Coba lagi.")`. Tapi jangan double-reply kalau sudah reply. Keep simple: catch di level handler utama? Tidak, biarkan python-telegram-bot default error handler. Tapi tambah logger.exception di setiap handler agar kita lihat error. *Opsional*, tapi tambahkan `try/except` di `cmd_*` yang melakukan DB call, dengan logger.exception dan user-friendly reply.

## Order ID Format
`ORD-{YYYYMMDD}-{4 hex uppercase}`. Contoh: `ORD-20260119-A3B2`. Generate pakai:
```python
import secrets
from datetime import datetime
order_id = f"ORD-{datetime.now().strftime('%Y%m%d')}-{secrets.token_hex(2).upper()}"
```

## Cleanup
- Folder lama `payments/`, `database/`, `__pycache__/` sudah dihapus.
- File lama: `bot.py`, `config.yaml`, `config.example.yaml`, `.env.example`, `docker-compose.yml`, `Dockerfile` dihapus.
- DB lama: `data/bot.db` di-rename ke `data/bot.db.old` (tidak dipakai, schema beda).

## Testing Plan
1. `cd /root/telegram-auto-order-bot && python3 -m venv venv && venv/bin/pip install -r requirements.txt`
2. `venv/bin/python -u bot.py`
3. Di Telegram: `/start` → `/katalog` → klik Beli → masukkan jumlah → Konfirmasi.
4. Admin: `/addproduct` (tambah 2 produk), `/listproducts`, lalu order sebagai user biasa, lalu `/orders`, klik Paid.
5. Broadcast: `/broadcast Halo semua`.
