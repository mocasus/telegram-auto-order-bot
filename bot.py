#!/usr/bin/env python3
"""
Telegram Auto Order Bot — Bot Telegram dengan integrasi pembayaran KlikQRIS.

Fitur:
- Katalog produk dengan kategori dan navigasi inline keyboard
- Keranjang belanja (tambah, hapus, kosongkan)
- Checkout dengan pembayaran QRIS
- Verifikasi pembayaran via polling + webhook callback
- Riwayat pesanan per user
- Panel admin untuk manajemen produk dan pesanan

Dibangun dengan python-telegram-bot v22+.
"""

import asyncio
import logging
import os
import re
import sys
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from telegram.constants import ParseMode

from database.models import get_db, Database
from payments.klikqris import (
    KlikQRIS,
    KlikQRISError,
    format_rupiah,
    generate_order_id,
)

# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

# ============================================================
# Conversation States (untuk admin add/edit product)
# ============================================================

(
    ADMIN_PROD_NAME,
    ADMIN_PROD_PRICE,
    ADMIN_PROD_DESC,
    ADMIN_PROD_CATEGORY,
    ADMIN_PROD_STOCK,
    ADMIN_PROD_EMOJI,
    ADMIN_PROD_CONFIRM,
) = range(7)

CHECKOUT_CONFIRM = 100

# ============================================================
# Config Loader
# ============================================================

def load_config(path: str = "config.yaml") -> dict:
    """Load konfigurasi dari YAML, dengan substitusi environment variable."""
    if not os.path.exists(path):
        logger.error("File konfigurasi tidak ditemukan: %s", path)
        sys.exit(1)

    with open(path, "r") as f:
        content = f.read()

    # Substitusi ${VAR} atau ${VAR:-default}
    def env_replace(match):
        expr = match.group(1)
        if ":-" in expr:
            var, default = expr.split(":-", 1)
            return os.environ.get(var.strip(), default.strip())
        return os.environ.get(expr, "")

    content = re.sub(r"\$\{([^}]+)\}", env_replace, content)
    return yaml.safe_load(content)


# ============================================================
# Config Global
# ============================================================

config_path = os.environ.get("CONFIG_PATH", "config.yaml")
CONFIG = load_config(config_path)

# ============================================================
# State Management — Keranjang Belanja (in-memory)
# ============================================================

# Format: {user_id: {product_id: {"product": {...}, "quantity": N}}}
user_carts: Dict[int, Dict[str, Dict[str, Any]]] = {}


def get_cart(user_id: int) -> Dict[str, Dict[str, Any]]:
    """Dapatkan keranjang user."""
    if user_id not in user_carts:
        user_carts[user_id] = {}
    return user_carts[user_id]


def add_to_cart(user_id: int, product: dict, quantity: int = 1):
    """Tambah produk ke keranjang."""
    cart = get_cart(user_id)
    pid = product["id"]
    if pid in cart:
        cart[pid]["quantity"] += quantity
    else:
        cart[pid] = {"product": product, "quantity": quantity}


def remove_from_cart(user_id: int, product_id: str):
    """Hapus produk dari keranjang."""
    cart = get_cart(user_id)
    cart.pop(product_id, None)


def clear_cart(user_id: int):
    """Kosongkan keranjang."""
    user_carts.pop(user_id, None)


def cart_total(user_id: int) -> int:
    """Hitung total harga keranjang."""
    cart = get_cart(user_id)
    return sum(item["product"]["price"] * item["quantity"] for item in cart.values())


def cart_items(user_id: int) -> List[Dict[str, Any]]:
    """Dapatkan list item di keranjang."""
    return [
        {
            "product_id": pid,
            "product_name": item["product"]["name"],
            "price": item["product"]["price"],
            "quantity": item["quantity"],
            "subtotal": item["product"]["price"] * item["quantity"],
        }
        for pid, item in get_cart(user_id).items()
    ]


# ============================================================
# KlikQRIS Client
# ============================================================

klikqris_client: Optional[KlikQRIS] = None


def get_klikqris() -> KlikQRIS:
    """Dapatkan instance KlikQRIS client."""
    global klikqris_client
    if klikqris_client is None:
        klikqris_client = KlikQRIS(
            api_key=CONFIG["klikqris"]["api_key"],
            merchant_id=CONFIG["klikqris"]["merchant_id"],
            mode=CONFIG["klikqris"]["mode"],
            timeout=CONFIG["klikqris"]["timeout"],
        )
    return klikqris_client


# ============================================================
# Database
# ============================================================

db: Optional[Database] = None


def get_database() -> Database:
    """Dapatkan instance database."""
    global db
    if db is None:
        db_path = CONFIG.get("database", {}).get("path", "data/bot.db")
        db = get_db(db_path)
        # Sinkronkan kategori dan produk dari config
        db.sync_categories(CONFIG.get("kategori", []))
        db.sync_products(CONFIG.get("produk", []))
    return db


# ============================================================
# Helpers
# ============================================================

def is_admin(user_id: int) -> bool:
    """Cek apakah user adalah admin."""
    admin_config = CONFIG.get("admin", {})
    if user_id == admin_config.get("user_id"):
        return True
    if user_id in admin_config.get("additional_ids", []):
        return True
    # Cek juga dari database
    d = get_database()
    return d.is_admin(user_id)


def get_user_name(update: Update) -> str:
    """Dapatkan nama user dari update."""
    user = update.effective_user
    if not user:
        return "Pengguna"
    if user.full_name:
        return user.full_name
    if user.first_name:
        return user.first_name
    return user.username or "Pengguna"


def get_message(key: str, **kwargs) -> str:
    """Dapatkan pesan dari config dengan substitusi."""
    msg = CONFIG.get("pesan", {}).get(key, "")
    return msg.format(**kwargs)


def build_main_menu(user_id: int) -> InlineKeyboardMarkup:
    """Buat inline keyboard menu utama."""
    buttons = [
        [InlineKeyboardButton("🛍️ Katalog Produk", callback_data="catalog")],
        [InlineKeyboardButton("🛒 Keranjang Saya", callback_data="cart:view")],
        [InlineKeyboardButton("📦 Pesanan Saya", callback_data="orders:my")],
        [InlineKeyboardButton("ℹ️ Bantuan", callback_data="help")],
    ]
    if is_admin(user_id):
        buttons.append([InlineKeyboardButton("⚙️ Panel Admin", callback_data="admin:panel")])
    return InlineKeyboardMarkup(buttons)


def build_category_menu(categories: List[Dict]) -> InlineKeyboardMarkup:
    """Buat inline keyboard daftar kategori."""
    buttons = []
    for cat in categories:
        buttons.append([
            InlineKeyboardButton(cat["name"], callback_data=f"cat:{cat['id']}")
        ])
    buttons.append([InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu")])
    return InlineKeyboardMarkup(buttons)


def build_product_list(products: List[Dict], category_id: str) -> InlineKeyboardMarkup:
    """Buat inline keyboard daftar produk dalam kategori."""
    buttons = []
    for prod in products:
        emoji = prod.get("emoji", "📦")
        name = prod["name"]
        price = format_rupiah(prod["price"])
        label = f"{emoji} {name} — {price}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"prod:{prod['id']}")])
    buttons.append([
        InlineKeyboardButton("🔙 Ke Kategori", callback_data="catalog"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu"),
    ])
    return InlineKeyboardMarkup(buttons)


def build_product_detail(product: dict) -> InlineKeyboardMarkup:
    """Buat inline keyboard detail produk."""
    buttons = [
        [
            InlineKeyboardButton("➖", callback_data=f"cart:add:{product['id']}:-1"),
            InlineKeyboardButton("➕ Tambah ke Keranjang", callback_data=f"cart:add:{product['id']}:1"),
            InlineKeyboardButton("➕➕", callback_data=f"cart:add:{product['id']}:5"),
        ],
        [
            InlineKeyboardButton("🔙 Ke Katalog", callback_data=f"cat:{product['category_id']}"),
            InlineKeyboardButton("🏠 Menu", callback_data="menu"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def build_cart_menu(user_id: int) -> InlineKeyboardMarkup:
    """Buat inline keyboard keranjang."""
    cart = get_cart(user_id)
    buttons = []

    if not cart:
        buttons.append([InlineKeyboardButton("🛍️ Lihat Katalog", callback_data="catalog")])
        buttons.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")])
        return InlineKeyboardMarkup(buttons)

    # Tombol per item
    for pid, item in cart.items():
        prod = item["product"]
        qty = item["quantity"]
        label = f"❌ {prod['name']} (x{qty})"
        buttons.append([InlineKeyboardButton(label, callback_data=f"cart:rem:{pid}")])

    buttons.append([InlineKeyboardButton("🗑️ Kosongkan Keranjang", callback_data="cart:clear")])

    total = cart_total(user_id)
    admin_fee = CONFIG.get("toko", {}).get("admin_fee", 0)
    tax_percent = CONFIG.get("toko", {}).get("tax_percent", 0)
    tax = int(total * tax_percent / 100)
    grand = total + admin_fee + tax

    label = f"💳 Checkout — {format_rupiah(grand)}"
    buttons.append([InlineKeyboardButton(label, callback_data="checkout:start")])
    buttons.append([
        InlineKeyboardButton("🛍️ Lanjut Belanja", callback_data="catalog"),
        InlineKeyboardButton("🏠 Menu", callback_data="menu"),
    ])

    return InlineKeyboardMarkup(buttons)


def build_checkout_confirm(user_id: int) -> InlineKeyboardMarkup:
    """Buat inline keyboard konfirmasi checkout."""
    total = cart_total(user_id)
    admin_fee = CONFIG.get("toko", {}).get("admin_fee", 0)
    tax_percent = CONFIG.get("toko", {}).get("tax_percent", 0)
    tax = int(total * tax_percent / 100)
    grand = total + admin_fee + tax

    buttons = [
        [InlineKeyboardButton(f"✅ Konfirmasi Pembayaran — {format_rupiah(grand)}", callback_data="checkout:confirm")],
        [InlineKeyboardButton("🔙 Kembali ke Keranjang", callback_data="cart:view")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")],
    ]
    return InlineKeyboardMarkup(buttons)


def build_order_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Buat inline keyboard untuk pesanan."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💳 Lihat Pembayaran", callback_data=f"pay:{order_id}")],
        [InlineKeyboardButton("🔄 Cek Status", callback_data=f"pay:check:{order_id}")],
        [InlineKeyboardButton("📦 Pesanan Saya", callback_data="orders:my")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")],
    ])


def build_payment_keyboard(order_id: str) -> InlineKeyboardMarkup:
    """Buat inline keyboard pembayaran."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔄 Cek Status Pembayaran", callback_data=f"pay:check:{order_id}")],
        [InlineKeyboardButton("📦 Lihat Pesanan", callback_data=f"order:{order_id}")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")],
    ])


def build_admin_menu() -> InlineKeyboardMarkup:
    """Buat inline keyboard panel admin."""
    counts = get_database().get_order_count_by_status()
    pending = counts.get("pending", 0)
    paid = counts.get("paid", 0)

    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📋 Semua Pesanan ({pending} pending)", callback_data="admin:orders")],
        [InlineKeyboardButton(f"✅ Pesanan Lunas ({paid})", callback_data="admin:orders:paid")],
        [InlineKeyboardButton("📦 Kelola Produk", callback_data="admin:products")],
        [InlineKeyboardButton("➕ Tambah Produk Baru", callback_data="admin:add_product")],
        [InlineKeyboardButton("📊 Ringkasan", callback_data="admin:summary")],
        [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")],
    ])


def build_admin_orders_keyboard(
    orders: list, page: int = 0, status: Optional[str] = None
) -> Tuple[str, InlineKeyboardMarkup]:
    """Buat inline keyboard daftar pesanan untuk admin."""
    per_page = 5
    total = len(orders)
    start = page * per_page
    page_orders = orders[start : start + per_page]

    text = f"📋 *Daftar Pesanan*"
    if status:
        text += f" (Status: {status})"
    text += f"\n\nTotal: {total} pesanan\n\n"

    buttons = []
    for order in page_orders:
        oid = order["id"][:20]
        status_emoji = {"pending": "⏳", "paid": "✅", "expired": "❌", "cancelled": "🚫"}.get(
            order["status"], "❓"
        )
        label = f"{status_emoji} {oid}... — {format_rupiah(order['grand_total'])}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"order:{order['id']}")])

    # Pagination
    nav = []
    if page > 0:
        cb = f"admin:orders:{status or 'all'}:{page - 1}"
        nav.append(InlineKeyboardButton("⬅️ Sebelumnya", callback_data=cb))
    if (page + 1) * per_page < total:
        cb = f"admin:orders:{status or 'all'}:{page + 1}"
        nav.append(InlineKeyboardButton("➡️ Selanjutnya", callback_data=cb))
    if nav:
        buttons.append(nav)

    buttons.append([InlineKeyboardButton("🔙 Panel Admin", callback_data="admin:panel")])

    return text, InlineKeyboardMarkup(buttons)


# ============================================================
# Command Handlers
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /start — pesan sambutan."""
    user = update.effective_user
    nama = get_user_name(update)
    toko = CONFIG.get("toko", {}).get("name", "Toko Online")

    # Daftarkan user ke database
    user_data = {
        "id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "full_name": user.full_name,
        "language_code": user.language_code,
    }
    get_database().get_or_create_user(user_data)

    text = f"""👋 *Halo {nama}!*

Selamat datang di *{toko}*!
Silakan pilih menu di bawah ini:

🛍️ *Katalog* — Lihat produk kami
🛒 *Keranjang* — Lihat keranjang belanja
📦 *Pesanan Saya* — Lacak pesanan Anda
ℹ️ *Bantuan* — Pusat bantuan"""

    await update.message.reply_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu(user.id),
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /bantuan."""
    text = """📖 *Pusat Bantuan*

🛍️ *Cara Belanja:*
1. Buka Katalog Produk
2. Pilih kategori dan produk
3. Tambahkan ke keranjang
4. Checkout dan lakukan pembayaran QRIS

💳 *Pembayaran:*
Kami menerima pembayaran melalui QRIS.
Setelah checkout, Anda akan menerima kode QR
yang dapat dipindai menggunakan aplikasi pembayaran
apa pun yang mendukung QRIS.

⏱️ *Batas Waktu Pembayaran:*
Pembayaran harus diselesaikan dalam 30 menit
setelah checkout.

📞 *Butuh bantuan?*
Hubungi admin melalui menu Bantuan."""
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def cmd_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler /cancel — batalkan operasi yang sedang berjalan."""
    await update.message.reply_text(
        "❌ Operasi dibatalkan.",
        reply_markup=build_main_menu(update.effective_user.id),
    )
    return ConversationHandler.END


# ============================================================
# Callback Query Handlers — Navigasi Utama
# ============================================================

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kembali ke menu utama."""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🏠 *Menu Utama*\nSilakan pilih:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu(query.from_user.id),
    )


async def handle_catalog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan daftar kategori."""
    query = update.callback_query
    await query.answer()

    categories = get_database().get_categories()
    if not categories:
        await query.edit_message_text(
            "📭 *Katalog kosong*\n\nBelum ada produk tersedia.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")
            ]]),
        )
        return

    await query.edit_message_text(
        "🛍️ *Katalog Produk*\n\nPilih kategori:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_category_menu(categories),
    )


async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan produk dalam kategori."""
    query = update.callback_query
    await query.answer()

    category_id = query.data.split(":", 1)[1]
    category = get_database().get_category(category_id)

    if not category:
        await query.answer("Kategori tidak ditemukan!", show_alert=True)
        return

    products = get_database().get_products_by_category(category_id)

    if not products:
        await query.edit_message_text(
            f"📭 *{category['name']}*\n\nBelum ada produk di kategori ini.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Ke Katalog", callback_data="catalog")],
                [InlineKeyboardButton("🏠 Menu", callback_data="menu")],
            ]),
        )
        return

    text = f"🛍️ *{category['name']}*\n\nPilih produk:"
    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_product_list(products, category_id),
    )


async def handle_product_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan detail produk."""
    query = update.callback_query
    await query.answer()

    product_id = query.data.split(":", 1)[1]
    product = get_database().get_product(product_id)

    if not product:
        await query.answer("Produk tidak ditemukan!", show_alert=True)
        return

    emoji = product.get("emoji", "📦")
    price = format_rupiah(product["price"])
    stock = product.get("stock", 0)

    text = f"""{emoji} *{product['name']}*

💰 Harga: {price}
📦 Stok: {stock} tersedia

📝 *Deskripsi:*
{product.get('description', 'Tidak ada deskripsi')}"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_product_detail(product),
    )


# ============================================================
# Callback Query Handlers — Keranjang
# ============================================================

async def handle_cart_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tambah produk ke keranjang."""
    query = update.callback_query

    parts = query.data.split(":")
    product_id = parts[2]
    qty = int(parts[3])

    product = get_database().get_product(product_id)
    if not product:
        await query.answer("Produk tidak tersedia!", show_alert=True)
        return

    if qty < 0:
        # Kurangi quantity (tombol minus)
        cart = get_cart(query.from_user.id)
        if product_id in cart:
            cart[product_id]["quantity"] = max(0, cart[product_id]["quantity"] + qty)
            if cart[product_id]["quantity"] <= 0:
                remove_from_cart(query.from_user.id, product_id)
            await query.answer(f"✅ Quantity dikurangi")
        else:
            await query.answer("Produk belum ada di keranjang")
    else:
        add_to_cart(query.from_user.id, product, qty)
        await query.answer(f"✅ Ditambahkan ke keranjang (x{qty})", show_alert=False)

    # Refresh product detail view
    await handle_product_detail(update, context)


async def handle_cart_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan isi keranjang."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cart = get_cart(user_id)

    if not cart:
        await query.edit_message_text(
            "🛒 *Keranjang Belanja*\n\nKeranjang Anda kosong.\nYuk, tambahin produk dulu!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_cart_menu(user_id),
        )
        return

    total = cart_total(user_id)
    admin_fee = CONFIG.get("toko", {}).get("admin_fee", 0)
    tax_percent = CONFIG.get("toko", {}).get("tax_percent", 0)
    tax = int(total * tax_percent / 100)
    grand = total + admin_fee + tax
    symbol = CONFIG.get("toko", {}).get("currency_symbol", "Rp")

    lines = ["🛒 *Keranjang Belanja*\n"]
    for pid, item in cart.items():
        prod = item["product"]
        qty = item["quantity"]
        subtotal = prod["price"] * qty
        lines.append(f"• {prod.get('emoji', '📦')} {prod['name']}")
        lines.append(f"  {qty} × {format_rupiah(prod['price'])} = {format_rupiah(subtotal)}")

    lines.append("")
    lines.append(f"📊 *Subtotal:* {format_rupiah(total)}")
    if admin_fee > 0:
        lines.append(f"💳 Biaya Admin: {format_rupiah(admin_fee)}")
    if tax > 0:
        lines.append(f"🧾 PPN ({tax_percent}%): {format_rupiah(tax)}")
    lines.append(f"💰 *Total:* {format_rupiah(grand)}")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_cart_menu(user_id),
    )


async def handle_cart_remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Hapus produk dari keranjang."""
    query = update.callback_query

    product_id = query.data.split(":", 2)[2]
    remove_from_cart(query.from_user.id, product_id)

    await query.answer("❌ Produk dihapus dari keranjang")

    # Refresh cart view
    await handle_cart_view(update, context)


async def handle_cart_clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kosongkan keranjang."""
    query = update.callback_query
    clear_cart(query.from_user.id)
    await query.answer("🗑️ Keranjang dikosongkan")

    await query.edit_message_text(
        "🛒 *Keranjang Belanja*\n\nKeranjang telah dikosongkan.",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_cart_menu(query.from_user.id),
    )


# ============================================================
# Callback Query Handlers — Checkout & Pembayaran
# ============================================================

async def handle_checkout_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai proses checkout — tampilkan ringkasan pesanan."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cart = get_cart(user_id)

    if not cart:
        await query.answer("Keranjang kosong!", show_alert=True)
        return

    total = cart_total(user_id)
    admin_fee = CONFIG.get("toko", {}).get("admin_fee", 0)
    tax_percent = CONFIG.get("toko", {}).get("tax_percent", 0)
    tax = int(total * tax_percent / 100)
    grand = total + admin_fee + tax
    symbol = CONFIG.get("toko", {}).get("currency_symbol", "Rp")

    lines = ["📋 *Konfirmasi Pesanan*\n"]
    lines.append("📦 *Item Pesanan:*")
    for pid, item in cart.items():
        prod = item["product"]
        qty = item["quantity"]
        subtotal = prod["price"] * qty
        lines.append(f"  • {prod['name']} ×{qty} = {format_rupiah(subtotal)}")

    lines.append("")
    lines.append(f"📊 Subtotal: {format_rupiah(total)}")
    if admin_fee > 0:
        lines.append(f"💳 Biaya Admin: {format_rupiah(admin_fee)}")
    if tax > 0:
        lines.append(f"🧾 PPN ({tax_percent}%): {format_rupiah(tax)}")
    lines.append(f"")
    lines.append(f"💰 *Total Pembayaran:* {format_rupiah(grand)}")
    lines.append("")
    lines.append("Klik *Konfirmasi Pembayaran* untuk melanjutkan.")

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_checkout_confirm(user_id),
    )


async def handle_checkout_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Proses checkout — buat pesanan dan generate QRIS."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    cart = get_cart(user_id)

    if not cart:
        await query.answer("Keranjang kosong!", show_alert=True)
        await query.edit_message_text(
            "❌ Keranjang kosong, tidak bisa checkout.",
            reply_markup=build_main_menu(user_id),
        )
        return

    # Hitung total
    total = cart_total(user_id)
    admin_fee = CONFIG.get("toko", {}).get("admin_fee", 0)
    tax_percent = CONFIG.get("toko", {}).get("tax_percent", 0)
    tax = int(total * tax_percent / 100)
    grand = total + admin_fee + tax

    # Generate order ID
    order_id = generate_order_id(user_id)

    # Siapkan item
    items = cart_items(user_id)

    # Simpan ke database
    d = get_database()
    d.create_order(order_id, user_id, items, total, admin_fee, tax)

    # Buat pembayaran QRIS
    await query.edit_message_text(
        "⏳ *Memproses pembayaran...*\n\nMohon tunggu sebentar.",
        parse_mode=ParseMode.MARKDOWN,
    )

    try:
        klik = get_klikqris()
        toko_name = CONFIG.get("toko", {}).get("name", "Toko Online")
        keterangan = f"Pembayaran di {toko_name} — {order_id}"

        result = await klik.create_qris(
            order_id=order_id,
            amount=grand,
            keterangan=keterangan,
        )

        qris_data = result.get("data", {})
        qris_url = qris_data.get("qris_url", "")
        qris_image = qris_data.get("qris_image", "")
        qris_raw = qris_data.get("qris_data", "")
        payment_id = qris_data.get("payment_id", order_id)

        # Update order dengan info pembayaran
        d.update_order_payment(
            order_id=order_id,
            payment_status="pending",
            payment_id=payment_id,
            qris_url=qris_url,
            qris_data=qris_raw,
            qris_image=qris_image,
        )

        # Catat payment
        d.create_payment(
            payment_id=payment_id,
            order_id=order_id,
            user_id=user_id,
            amount=grand,
            qris_url=qris_url,
            qris_data=qris_raw,
            qris_image=qris_image,
        )

        # Kosongkan keranjang
        clear_cart(user_id)

        # Tampilkan QRIS
        lines = [
            "✅ *Pesanan Berhasil Dibuat!*\n",
            f"📦 *Order ID:* `{order_id}`",
            f"💰 *Total:* {format_rupiah(grand)}",
            f"⏱️ *Batas Waktu:* 30 menit",
            "",
            "📱 *Cara Membayar:*",
            "1. Buka aplikasi pembayaran (GoPay, OVO, DANA, dll)",
            "2. Pilih menu *Scan QRIS*",
            "3. Scan kode QR di bawah ini",
            "4. Konfirmasi pembayaran",
            "",
            "💡 *Tips:* Klik tombol di bawah untuk",
            "mengecek status pembayaran kapan saja.",
        ]

        if qris_image:
            # Jika ada gambar QR, kirim sebagai foto
            await query.message.reply_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
            )
            await query.message.reply_photo(
                photo=qris_image,
                caption=f"💳 *QRIS Pembayaran*\n\nTotal: {format_rupiah(grand)}\nOrder ID: `{order_id}`",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=build_payment_keyboard(order_id),
            )
            # Remove the "processing" message
            await query.delete_message()

            # Schedule polling
            asyncio.create_task(
                poll_payment_status(context, user_id, order_id, payment_id, grand)
            )
        elif qris_raw:
            # Kirim data QRIS sebagai teks
            lines.append("")
            lines.append("📋 *Data QRIS:*")
            lines.append(f"`{qris_raw}`")
            lines.append("")
            lines.append("Salin data di atas ke aplikasi yang mendukung QRIS.")

            await query.edit_message_text(
                "\n".join(lines),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=build_payment_keyboard(order_id),
            )
        else:
            await query.edit_message_text(
                "\n".join(lines) + "\n\n⚠️ Gagal generate QR code. Coba lagi nanti.",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=build_payment_keyboard(order_id),
            )

    except KlikQRISError as e:
        logger.error("Gagal membuat QRIS: %s", e)
        # Rollback: hapus order
        d.update_order_status(order_id, "failed")
        # Kembalikan stok
        for item in items:
            d.update_stock(item["product_id"], item["quantity"])

        await query.edit_message_text(
            f"❌ *Gagal membuat pembayaran*\n\nTerjadi kesalahan: {e}\n\nSilakan coba lagi nanti.",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_main_menu(user_id),
        )


async def poll_payment_status(
    context: ContextTypes.DEFAULT_TYPE,
    user_id: int,
    order_id: str,
    payment_id: str,
    amount: int,
):
    """Polling status pembayaran secara berkala."""
    polling_interval = CONFIG.get("klikqris", {}).get("polling_interval", 10)
    max_attempts = CONFIG.get("klikqris", {}).get("max_polling_attempts", 30)

    for attempt in range(max_attempts):
        await asyncio.sleep(polling_interval)

        try:
            klik = get_klikqris()
            result = await klik.check_status(order_id)
            data = result.get("data", {})
            status = data.get("payment_status", "pending")

            logger.info(
                "Polling #%d: order=%s status=%s",
                attempt + 1, order_id, status,
            )

            if status == "paid":
                # Update database
                d = get_database()
                d.update_order_payment(order_id, "paid", payment_id)
                d.update_payment_status(payment_id, "paid")

                # Notifikasi user
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"""✅ *Pembayaran Berhasil!*

📦 Order ID: `{order_id}`
💰 Jumlah: {format_rupiah(amount)}

Pesanan Anda sedang diproses.
Terima kasih telah berbelanja! 🎉""",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception as e:
                    logger.error("Gagal kirim notifikasi pembayaran: %s", e)

                return

            elif status in ("expired", "failed"):
                d = get_database()
                d.update_order_payment(order_id, status, payment_id)
                d.update_payment_status(payment_id, status)

                # Kembalikan stok
                order = d.get_order(order_id)
                if order:
                    for item in order.get("items", []):
                        d.update_stock(item["product_id"], item["quantity"])

                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=f"""⏰ *Pembayaran Kedaluwarsa*

📦 Order ID: `{order_id}`
💰 Jumlah: {format_rupiah(amount)}

Pesanan dibatalkan karena melebihi batas waktu.
Silakan buat pesanan baru. 🛍️""",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception as e:
                    logger.error("Gagal kirim notifikasi expired: %s", e)

                return

        except Exception as e:
            logger.error("Error saat polling %s: %s", order_id, e)


async def handle_payment_view(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan detail pembayaran."""
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":", 1)[1]

    d = get_database()
    order = d.get_order(order_id)

    if not order:
        await query.answer("Pesanan tidak ditemukan!", show_alert=True)
        return

    payment = d.get_payment_by_order(order_id)
    qris_data = order.get("qris_data", "") or (payment.get("qris_data", "") if payment else "")
    qris_image = order.get("qris_image", "") or (payment.get("qris_image", "") if payment else "")

    text = f"""💳 *Pembayaran QRIS*

📦 Order ID: `{order_id}`
💰 Total: {format_rupiah(order['grand_total'])}
📊 Status: {order.get('payment_status', 'unpaid').upper()}

📋 *Data QRIS:*
`{qris_data or 'Tidak tersedia'}`

💡 Scan atau salin data QRIS di atas
menggunakan aplikasi pembayaran Anda."""

    if qris_image:
        await query.message.reply_photo(
            photo=qris_image,
            caption=f"💳 QRIS — {format_rupiah(order['grand_total'])}",
            reply_markup=build_payment_keyboard(order_id),
        )
        await query.delete_message()
    else:
        await query.edit_message_text(
            text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_payment_keyboard(order_id),
        )


async def handle_payment_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek status pembayaran manual."""
    query = update.callback_query
    await query.answer("🔄 Mengecek status...")

    order_id = query.data.split(":", 2)[2]

    try:
        klik = get_klikqris()
        result = await klik.check_status(order_id)
        data = result.get("data", {})
        status = data.get("payment_status", "unknown")

        status_map = {
            "pending": "⏳ PENDING",
            "paid": "✅ LUNAS",
            "expired": "❌ KEDALUWARSA",
            "failed": "🚫 GAGAL",
        }
        status_label = status_map.get(status, status.upper())

        d = get_database()
        order = d.get_order(order_id)

        await query.edit_message_text(
            f"""🔄 *Status Pembayaran*

📦 Order ID: `{order_id}`
💰 Total: {format_rupiah(order['grand_total']) if order else '—'}
📊 Status: *{status_label}*

{f"⏱️ Waktu pembayaran: 30 menit setelah checkout" if status == "pending" else ""}""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_payment_keyboard(order_id),
        )

        # Jika sudah paid, update database
        if status == "paid":
            payment = d.get_payment_by_order(order_id)
            if payment:
                d.update_order_payment(order_id, "paid", payment["id"])
                d.update_payment_status(payment["id"], "paid")

    except Exception as e:
        await query.edit_message_text(
            f"⚠️ Gagal mengecek status: {e}\n\nSilakan coba lagi nanti.",
            reply_markup=build_payment_keyboard(order_id),
        )


# ============================================================
# Callback Query Handlers — Pesanan (Order History)
# ============================================================

async def handle_orders_my(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan riwayat pesanan user."""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    d = get_database()
    orders = d.get_user_orders(user_id, limit=10)

    if not orders:
        await query.edit_message_text(
            "📦 *Pesanan Saya*\n\nBelum ada pesanan.\nYuk, belanja dulu! 🛍️",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🛍️ Lihat Katalog", callback_data="catalog")],
                [InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")],
            ]),
        )
        return

    status_emoji = {
        "pending": "⏳", "paid": "✅", "expired": "❌",
        "cancelled": "🚫", "failed": "⚠️",
    }

    lines = ["📦 *Pesanan Saya*\n"]
    buttons = []

    for order in orders[:10]:
        oid = order["id"][:20]
        emoji = status_emoji.get(order["status"], "❓")
        status_label = {
            "pending": "Menunggu Bayar",
            "paid": "Lunas",
            "expired": "Kedaluwarsa",
            "cancelled": "Dibatalkan",
            "failed": "Gagal",
        }.get(order["status"], order["status"])

        lines.append(
            f"{emoji} `{oid}...` — {format_rupiah(order['grand_total'])} ({status_label})"
        )
        buttons.append([
            InlineKeyboardButton(
                f"{emoji} {oid}...",
                callback_data=f"order:{order['id']}",
            )
        ])

    buttons.append([InlineKeyboardButton("🏠 Menu Utama", callback_data="menu")])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_order_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan detail pesanan."""
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":", 1)[1]
    d = get_database()
    order = d.get_order(order_id)

    if not order:
        await query.answer("Pesanan tidak ditemukan!", show_alert=True)
        return

    status_emoji = {
        "pending": "⏳", "paid": "✅", "expired": "❌",
        "cancelled": "🚫", "failed": "⚠️",
    }
    emoji = status_emoji.get(order["status"], "❓")
    status_label = {
        "pending": "Menunggu Pembayaran",
        "paid": "Lunas",
        "expired": "Kedaluwarsa",
        "cancelled": "Dibatalkan",
        "failed": "Gagal",
    }.get(order["status"], order["status"])

    lines = [
        f"📦 *Detail Pesanan*",
        f"",
        f"🆔 Order ID: `{order['id']}`",
        f"📊 Status: {emoji} {status_label}",
        f"💳 Pembayaran: {order.get('payment_status', 'unpaid').upper()}",
        f"",
        f"📋 *Item Pesanan:*",
    ]

    for item in order.get("items", []):
        lines.append(
            f"  • {item['product_name']} ×{item['quantity']} = {format_rupiah(item['subtotal'])}"
        )

    lines.append("")
    lines.append(f"📊 Subtotal: {format_rupiah(order['total_amount'])}")
    if order.get("admin_fee", 0) > 0:
        lines.append(f"💳 Biaya Admin: {format_rupiah(order['admin_fee'])}")
    if order.get("tax_amount", 0) > 0:
        lines.append(f"🧾 PPN: {format_rupiah(order['tax_amount'])}")
    lines.append(f"💰 *Total:* {format_rupiah(order['grand_total'])}")
    lines.append(f"")
    if order.get("created_at"):
        lines.append(f"📅 Dibuat: {order['created_at']}")
    if order.get("paid_at"):
        lines.append(f"✅ Dibayar: {order['paid_at']}")

    user_id = query.from_user.id

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_order_keyboard(order_id),
    )


# ============================================================
# Admin Panel Handlers
# ============================================================

async def handle_admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan panel admin."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("Akses ditolak!", show_alert=True)
        return

    await query.edit_message_text(
        "⚙️ *Panel Admin*\n\nPilih menu:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_admin_menu(),
    )


async def handle_admin_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan semua pesanan (admin)."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("Akses ditolak!", show_alert=True)
        return

    parts = query.data.split(":")
    status = None
    page = 0

    if len(parts) >= 4:
        status = parts[2] if parts[2] != "all" else None
        page = int(parts[3])

    d = get_database()
    orders = d.get_all_orders(status=status, limit=100)

    text, markup = build_admin_orders_keyboard(orders, page, status)

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=markup,
    )


async def handle_admin_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan daftar produk untuk admin."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("Akses ditolak!", show_alert=True)
        return

    d = get_database()
    products = d.get_all_products()

    text = "📦 *Kelola Produk*\n\n"
    buttons = []

    for prod in products[:20]:
        emoji = prod.get("emoji", "📦")
        text += f"{emoji} {prod['name']} — {format_rupiah(prod['price'])} (Stok: {prod.get('stock', 0)})\n"

    buttons.append([InlineKeyboardButton("➕ Tambah Produk", callback_data="admin:add_product")])
    buttons.append([InlineKeyboardButton("🔙 Panel Admin", callback_data="admin:panel")])

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def handle_admin_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tampilkan ringkasan toko."""
    query = update.callback_query
    await query.answer()

    if not is_admin(query.from_user.id):
        await query.answer("Akses ditolak!", show_alert=True)
        return

    d = get_database()
    counts = d.get_order_count_by_status()

    total_orders = sum(counts.values())
    pending = counts.get("pending", 0)
    paid = counts.get("paid", 0)
    expired = counts.get("expired", 0)

    total_revenue = 0
    paid_orders = d.get_all_orders(status="paid", limit=1000)
    for o in paid_orders:
        total_revenue += o["grand_total"]

    products = d.get_all_products()

    text = f"""📊 *Ringkasan Toko*

📦 *Pesanan:*
  • Total: {total_orders}
  • Pending: {pending}
  • Lunas: {paid}
  • Kedaluwarsa: {expired}

💰 *Pendapatan (Lunas):* {format_rupiah(total_revenue)}

🛍️ *Produk Aktif:* {len(products)}

👥 *Mode:* {CONFIG.get('klikqris', {}).get('mode', 'sandbox')}"""

    await query.edit_message_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Panel Admin", callback_data="admin:panel")],
        ]),
    )


# ============================================================
# Admin Conversation — Tambah Produk Baru
# ============================================================

async def admin_add_product_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mulai flow tambah produk (admin)."""
    query = update.callback_query

    if not is_admin(query.from_user.id):
        await query.answer("Akses ditolak!", show_alert=True)
        return ConversationHandler.END

    await query.answer()
    await query.edit_message_text(
        "➕ *Tambah Produk Baru*\n\n"
        "Masukkan *nama produk*:\n\n"
        "_Ketik /cancel untuk membatalkan_",
        parse_mode=ParseMode.MARKDOWN,
    )

    return ADMIN_PROD_NAME


async def admin_add_product_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima nama produk."""
    name = update.message.text.strip()
    context.user_data["admin_new_product"] = {"name": name}

    await update.message.reply_text(
        f"📝 Nama: *{name}*\n\nMasukkan *harga* (angka, dalam Rupiah):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_PROD_PRICE


async def admin_add_product_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima harga produk."""
    try:
        price = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text(
            "❌ Harga harus berupa angka. Coba lagi:",
        )
        return ADMIN_PROD_PRICE

    context.user_data["admin_new_product"]["price"] = price

    await update.message.reply_text(
        f"💰 Harga: *{format_rupiah(price)}*\n\nMasukkan *deskripsi* produk (atau kirim '-' untuk kosong):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_PROD_DESC


async def admin_add_product_desc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima deskripsi produk."""
    desc = update.message.text.strip()
    if desc == "-":
        desc = ""
    context.user_data["admin_new_product"]["description"] = desc

    # Tampilkan kategori
    d = get_database()
    cats = d.get_categories()
    cat_list = "\n".join([f"• `{c['id']}` — {c['name']}" for c in cats])

    await update.message.reply_text(
        f"📂 Pilih *kategori*:\n\n{cat_list}\n\n"
        "Ketik *ID kategori* (misal: `makanan`):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_PROD_CATEGORY


async def admin_add_product_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima kategori produk."""
    cat_id = update.message.text.strip().lower()
    d = get_database()
    cat = d.get_category(cat_id)

    if not cat:
        cats = d.get_categories()
        cat_list = "\n".join([f"• `{c['id']}` — {c['name']}`" for c in cats])
        await update.message.reply_text(
            f"❌ Kategori `{cat_id}` tidak ditemukan.\n\nPilih dari:\n{cat_list}\n\nCoba lagi:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return ADMIN_PROD_CATEGORY

    context.user_data["admin_new_product"]["category_id"] = cat_id

    await update.message.reply_text(
        f"📂 Kategori: *{cat['name']}*\n\nMasukkan *jumlah stok* (angka):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_PROD_STOCK


async def admin_add_product_stock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima stok produk."""
    try:
        stock = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Stok harus berupa angka. Coba lagi:")
        return ADMIN_PROD_STOCK

    context.user_data["admin_new_product"]["stock"] = stock

    await update.message.reply_text(
        f"📦 Stok: *{stock}*\n\nMasukkan *emoji* untuk produk (atau '-' untuk default 📦):",
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_PROD_EMOJI


async def admin_add_product_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Terima emoji produk."""
    emoji = update.message.text.strip()
    if emoji == "-":
        emoji = "📦"
    context.user_data["admin_new_product"]["emoji"] = emoji

    prod = context.user_data["admin_new_product"]
    summary = f"""📋 *Konfirmasi Produk Baru*

📝 Nama: *{prod['name']}*
💰 Harga: {format_rupiah(prod['price'])}
📝 Deskripsi: {prod.get('description', '-') or '-'}
📂 Kategori: `{prod.get('category_id', '-')}`
📦 Stok: {prod.get('stock', 0)}
{prod.get('emoji', '📦')} Emoji: {prod.get('emoji', '📦')}

Kirim *YA* untuk menyimpan, atau *TIDAK* untuk membatalkan."""

    await update.message.reply_text(
        summary,
        parse_mode=ParseMode.MARKDOWN,
    )
    return ADMIN_PROD_CONFIRM


async def admin_add_product_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Simpan atau batalkan produk baru."""
    text = update.message.text.strip().upper()

    if text == "YA":
        prod = context.user_data["admin_new_product"]
        import random
        import string

        pid = prod["name"].lower().replace(" ", "-")[:30]

        d = get_database()
        d.conn.execute(
            """INSERT OR REPLACE INTO products
               (id, name, price, description, category_id, stock, emoji, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                pid,
                prod["name"],
                prod["price"],
                prod.get("description", ""),
                prod.get("category_id", ""),
                prod.get("stock", 0),
                prod.get("emoji", "📦"),
            ),
        )
        d.conn.commit()

        await update.message.reply_text(
            f"✅ *Produk berhasil ditambahkan!*\n\nID: `{pid}`\nNama: {prod['name']}",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=build_admin_menu(),
        )
    else:
        await update.message.reply_text(
            "❌ Penambahan produk dibatalkan.",
            reply_markup=build_admin_menu(),
        )

    context.user_data.pop("admin_new_product", None)
    return ConversationHandler.END


# ============================================================
# Webhook Handler (untuk callback KlikQRIS)
# ============================================================

async def handle_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle webhook callback dari KlikQRIS (jika menggunakan polling mode)."""
    # Webhook sebenarnya di-handle oleh server HTTP terpisah.
    # Handler ini untuk fallback jika diperlukan.
    pass


# ============================================================
# Error Handler
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Log error dan kirim pesan ke user."""
    logger.error("Exception saat menangani update:", exc_info=context.error)

    if update and isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ Maaf, terjadi kesalahan. Silakan coba lagi nanti.\n"
                "Gunakan /start untuk kembali ke menu utama.",
            )
        except Exception:
            pass


# ============================================================
# Application Builder
# ============================================================

def build_application() -> Application:
    """Bangun dan konfigurasi bot application."""

    token = CONFIG["bot"]["token"]
    if not token or token == "YOUR_BOT_TOKEN_HERE" or token.startswith("${"):
        logger.error(
            "Token bot tidak valid! Edit config.yaml atau set "
            "TELEGRAM_BOT_TOKEN environment variable."
        )
        sys.exit(1)

    app = (
        ApplicationBuilder()
        .token(token)
        .build()
    )

    # Command handlers
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("bantuan", cmd_help))
    app.add_handler(CommandHandler("menu", cmd_start))

    # Admin Conversation — tambah produk
    admin_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(admin_add_product_start, pattern="^admin:add_product$"),
        ],
        states={
            ADMIN_PROD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_name),
            ],
            ADMIN_PROD_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_price),
            ],
            ADMIN_PROD_DESC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_desc),
            ],
            ADMIN_PROD_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_category),
            ],
            ADMIN_PROD_STOCK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_stock),
            ],
            ADMIN_PROD_EMOJI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_emoji),
            ],
            ADMIN_PROD_CONFIRM: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_add_product_confirm),
            ],
        },
        fallbacks=[CommandHandler("cancel", cmd_cancel)],
    )
    app.add_handler(admin_conv)

    # Callback query handlers — urutan penting (pattern spesifik dulu)

    # Navigasi utama
    app.add_handler(CallbackQueryHandler(handle_menu, pattern="^menu$"))
    app.add_handler(CallbackQueryHandler(handle_catalog, pattern="^catalog$"))
    app.add_handler(CallbackQueryHandler(handle_category, pattern="^cat:"))
    app.add_handler(CallbackQueryHandler(handle_product_detail, pattern="^prod:"))

    # Bantuan
    app.add_handler(CallbackQueryHandler(
        lambda u, c: cmd_help(u, c), pattern="^help$"
    ))

    # Keranjang
    app.add_handler(CallbackQueryHandler(handle_cart_add, pattern="^cart:add:"))
    app.add_handler(CallbackQueryHandler(handle_cart_remove, pattern="^cart:rem:"))
    app.add_handler(CallbackQueryHandler(handle_cart_clear, pattern="^cart:clear$"))
    app.add_handler(CallbackQueryHandler(handle_cart_view, pattern="^cart:view$"))

    # Checkout
    app.add_handler(CallbackQueryHandler(handle_checkout_start, pattern="^checkout:start$"))
    app.add_handler(CallbackQueryHandler(handle_checkout_confirm, pattern="^checkout:confirm$"))

    # Pembayaran
    app.add_handler(CallbackQueryHandler(handle_payment_view, pattern="^pay:[^:]+$"))
    app.add_handler(CallbackQueryHandler(handle_payment_check, pattern="^pay:check:"))

    # Pesanan
    app.add_handler(CallbackQueryHandler(handle_orders_my, pattern="^orders:my$"))
    app.add_handler(CallbackQueryHandler(handle_order_detail, pattern="^order:"))

    # Admin
    app.add_handler(CallbackQueryHandler(handle_admin_panel, pattern="^admin:panel$"))
    app.add_handler(CallbackQueryHandler(handle_admin_orders, pattern="^admin:orders"))
    app.add_handler(CallbackQueryHandler(handle_admin_products, pattern="^admin:products$"))
    app.add_handler(CallbackQueryHandler(handle_admin_summary, pattern="^admin:summary$"))

    # Error handler
    app.add_error_handler(error_handler)

    return app


# ============================================================
# Main
# ============================================================

def main():
    """Entry point bot."""
    logger.info("=" * 50)
    logger.info("Telegram Auto Order Bot")
    logger.info("=" * 50)

    # Validasi konfigurasi
    token = CONFIG.get("bot", {}).get("token", "")
    if not token or token.startswith("${"):
        logger.error("Token bot tidak dikonfigurasi!")
        logger.error("Set TELEGRAM_BOT_TOKEN di environment atau edit config.yaml")
        sys.exit(1)

    api_key = CONFIG.get("klikqris", {}).get("api_key", "")
    if api_key.startswith("${"):
        logger.warning("KlikQRIS API key menggunakan env var — pastikan sudah di-set")

    mode = CONFIG.get("klikqris", {}).get("mode", "sandbox")
    logger.info("Mode KlikQRIS: %s", mode)
    logger.info("Mode Webhook: %s", CONFIG.get("webhook", {}).get("enabled", False))

    # Inisialisasi database
    d = get_database()
    d.sync_categories(CONFIG.get("kategori", []))
    d.sync_products(CONFIG.get("produk", []))
    logger.info("Database siap — %s", CONFIG.get("database", {}).get("path", "data/bot.db"))

    # Build dan jalankan bot
    app = build_application()

    webhook_config = CONFIG.get("webhook", {})

    if webhook_config.get("enabled"):
        webhook_url = webhook_config.get("url", "")
        webhook_port = webhook_config.get("port", 8443)

        logger.info("Menjalankan bot dengan webhook di %s", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=webhook_port,
            url_path="webhook",
            webhook_url=webhook_url,
        )
    else:
        logger.info("Menjalankan bot dengan polling...")
        app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
