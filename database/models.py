"""Database models untuk Telegram Auto Order Bot.

Menggunakan SQLite untuk penyimpanan data.
"""

import sqlite3
import os
import threading
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


class Database:
    """Manajer database SQLite thread-safe."""

    def __init__(self, db_path: str = "data/bot.db"):
        """Inisialisasi database.

        Args:
            db_path: Path ke file SQLite
        """
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    @property
    def conn(self) -> sqlite3.Connection:
        """Koneksi database per-thread."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
            self._local.conn.execute("PRAGMA journal_mode=WAL")
            self._local.conn.execute("PRAGMA foreign_keys=ON")
        return self._local.conn

    def _init_db(self):
        """Buat tabel jika belum ada."""
        conn = self.conn
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                user_id         INTEGER PRIMARY KEY,
                username        TEXT,
                first_name      TEXT,
                last_name       TEXT,
                full_name       TEXT,
                language_code   TEXT,
                is_admin        INTEGER DEFAULT 0,
                is_banned       INTEGER DEFAULT 0,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id              TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                description     TEXT,
                sort_order      INTEGER DEFAULT 0,
                is_active       INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS products (
                id              TEXT PRIMARY KEY,
                name            TEXT NOT NULL,
                price           INTEGER NOT NULL,
                description     TEXT,
                category_id     TEXT,
                stock           INTEGER DEFAULT 0,
                emoji           TEXT DEFAULT '📦',
                is_active       INTEGER DEFAULT 1,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id)
                    ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id              TEXT PRIMARY KEY,
                user_id         INTEGER NOT NULL,
                status          TEXT DEFAULT 'pending',
                total_amount    INTEGER NOT NULL,
                admin_fee       INTEGER DEFAULT 0,
                tax_amount      INTEGER DEFAULT 0,
                grand_total     INTEGER NOT NULL,
                payment_method  TEXT DEFAULT 'qris',
                payment_id      TEXT,
                payment_status  TEXT DEFAULT 'unpaid',
                payment_url     TEXT,
                qris_image      TEXT,
                qris_data       TEXT,
                notes           TEXT,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                paid_at         TIMESTAMP,
                expired_at      TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id        TEXT NOT NULL,
                product_id      TEXT NOT NULL,
                product_name    TEXT NOT NULL,
                price           INTEGER NOT NULL,
                quantity        INTEGER NOT NULL DEFAULT 1,
                subtotal        INTEGER NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS payments (
                id              TEXT PRIMARY KEY,
                order_id        TEXT NOT NULL,
                user_id         INTEGER NOT NULL,
                amount          INTEGER NOT NULL,
                status          TEXT DEFAULT 'pending',
                qris_url        TEXT,
                qris_data       TEXT,
                qris_image      TEXT,
                expired_at      TIMESTAMP,
                paid_at         TIMESTAMP,
                created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            );

            CREATE INDEX IF NOT EXISTS idx_orders_user_id ON orders(user_id);
            CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
            CREATE INDEX IF NOT EXISTS idx_payments_order_id ON payments(order_id);
            CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
        """)
        conn.commit()

    # =================================================================
    # Users
    # =================================================================

    def get_or_create_user(self, user_data: dict) -> Dict[str, Any]:
        """Dapatkan atau buat user baru.

        Args:
            user_data: Data user dari Telegram (id, username, first_name, ...)

        Returns:
            Dict data user
        """
        user_id = user_data.get("id", user_data.get("user_id"))
        existing = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()

        if existing:
            self.conn.execute(
                """UPDATE users SET
                    username = ?, first_name = ?, last_name = ?,
                    full_name = ?, language_code = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?""",
                (
                    user_data.get("username"),
                    user_data.get("first_name"),
                    user_data.get("last_name"),
                    user_data.get("full_name", user_data.get("first_name", "")),
                    user_data.get("language_code"),
                    user_id,
                ),
            )
            self.conn.commit()
            return dict(existing)

        full_name = user_data.get("full_name", "")
        if not full_name:
            first = user_data.get("first_name", "")
            last = user_data.get("last_name", "")
            full_name = f"{first} {last}".strip()

        self.conn.execute(
            """INSERT INTO users (user_id, username, first_name, last_name,
               full_name, language_code)
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                user_data.get("username"),
                user_data.get("first_name"),
                user_data.get("last_name"),
                full_name,
                user_data.get("language_code"),
            ),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else {}

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Dapatkan user berdasarkan ID."""
        row = self.conn.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return dict(row) if row else None

    def is_admin(self, user_id: int) -> bool:
        """Cek apakah user adalah admin."""
        row = self.conn.execute(
            "SELECT is_admin FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        return bool(row and row["is_admin"])

    def set_admin(self, user_id: int, is_admin: bool = True):
        """Set status admin user."""
        self.conn.execute(
            "UPDATE users SET is_admin = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
            (int(is_admin), user_id),
        )
        self.conn.commit()

    # =================================================================
    # Categories
    # =================================================================

    def sync_categories(self, categories: List[dict]):
        """Sinkronkan kategori dari config ke database."""
        for i, cat in enumerate(categories):
            self.conn.execute(
                """INSERT OR REPLACE INTO categories
                   (id, name, description, sort_order, is_active)
                VALUES (?, ?, ?, ?, 1)""",
                (cat["id"], cat["nama"], cat.get("deskripsi", ""), i),
            )
        self.conn.commit()

    def get_categories(self) -> List[Dict[str, Any]]:
        """Dapatkan semua kategori aktif."""
        rows = self.conn.execute(
            "SELECT * FROM categories WHERE is_active = 1 ORDER BY sort_order"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_category(self, category_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan kategori berdasarkan ID."""
        row = self.conn.execute(
            "SELECT * FROM categories WHERE id = ? AND is_active = 1",
            (category_id,),
        ).fetchone()
        return dict(row) if row else None

    # =================================================================
    # Products
    # =================================================================

    def sync_products(self, products: List[dict]):
        """Sinkronkan produk dari config ke database."""
        for prod in products:
            self.conn.execute(
                """INSERT OR REPLACE INTO products
                   (id, name, price, description, category_id, stock, emoji, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1)""",
                (
                    prod["id"],
                    prod["nama"],
                    prod["harga"],
                    prod.get("deskripsi", ""),
                    prod.get("kategori"),
                    prod.get("stok", 0),
                    prod.get("emoji", "📦"),
                ),
            )
        self.conn.commit()

    def get_products_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """Dapatkan produk berdasarkan kategori."""
        rows = self.conn.execute(
            """SELECT * FROM products
            WHERE category_id = ? AND is_active = 1 AND stock > 0
            ORDER BY name""",
            (category_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan produk berdasarkan ID."""
        row = self.conn.execute(
            "SELECT * FROM products WHERE id = ? AND is_active = 1",
            (product_id,),
        ).fetchone()
        return dict(row) if row else None

    def get_all_products(self) -> List[Dict[str, Any]]:
        """Dapatkan semua produk aktif."""
        rows = self.conn.execute(
            "SELECT * FROM products WHERE is_active = 1 ORDER BY name"
        ).fetchall()
        return [dict(r) for r in rows]

    def update_stock(self, product_id: str, quantity_change: int):
        """Update stok produk (negatif untuk mengurangi)."""
        self.conn.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (quantity_change, product_id),
        )
        self.conn.commit()

    # =================================================================
    # Orders
    # =================================================================

    def create_order(
        self,
        order_id: str,
        user_id: int,
        items: List[dict],
        total_amount: int,
        admin_fee: int = 0,
        tax_amount: int = 0,
    ) -> str:
        """Buat pesanan baru.

        Args:
            order_id: ID pesanan unik
            user_id: ID user Telegram
            items: List item [{product_id, product_name, price, quantity, subtotal}]
            total_amount: Total sebelum fee
            admin_fee: Biaya admin
            tax_amount: Pajak

        Returns:
            order_id
        """
        grand_total = total_amount + admin_fee + tax_amount
        from datetime import timedelta

        expired_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        self.conn.execute(
            """INSERT INTO orders
               (id, user_id, status, total_amount, admin_fee, tax_amount,
                grand_total, expired_at)
            VALUES (?, ?, 'pending', ?, ?, ?, ?, ?)""",
            (order_id, user_id, total_amount, admin_fee, tax_amount, grand_total, expired_at),
        )

        for item in items:
            self.conn.execute(
                """INSERT INTO order_items
                   (order_id, product_id, product_name, price, quantity, subtotal)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    order_id,
                    item["product_id"],
                    item["product_name"],
                    item["price"],
                    item["quantity"],
                    item["subtotal"],
                ),
            )
            # Kurangi stok
            self.update_stock(item["product_id"], -item["quantity"])

        self.conn.commit()
        return order_id

    def get_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan pesanan beserta item-nya."""
        order = self.conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()

        if not order:
            return None

        items = self.conn.execute(
            "SELECT * FROM order_items WHERE order_id = ?", (order_id,)
        ).fetchall()

        result = dict(order)
        result["items"] = [dict(i) for i in items]
        return result

    def get_user_orders(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Dapatkan daftar pesanan user."""
        rows = self.conn.execute(
            """SELECT * FROM orders
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?""",
            (user_id, limit, offset),
        ).fetchall()

        orders = []
        for row in rows:
            order = dict(row)
            items = self.conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
            ).fetchall()
            order["items"] = [dict(i) for i in items]
            orders.append(order)

        return orders

    def get_all_orders(
        self, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Dapatkan semua pesanan (admin)."""
        if status:
            rows = self.conn.execute(
                """SELECT * FROM orders
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?""",
                (status, limit, offset),
            ).fetchall()
        else:
            rows = self.conn.execute(
                """SELECT * FROM orders
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?""",
                (limit, offset),
            ).fetchall()

        orders = []
        for row in rows:
            order = dict(row)
            items = self.conn.execute(
                "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
            ).fetchall()
            order["items"] = [dict(i) for i in items]
            orders.append(order)

        return orders

    def update_order_status(self, order_id: str, status: str):
        """Update status pesanan."""
        self.conn.execute(
            "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, order_id),
        )
        self.conn.commit()

    def update_order_payment(
        self,
        order_id: str,
        payment_status: str,
        payment_id: Optional[str] = None,
        qris_url: Optional[str] = None,
        qris_data: Optional[str] = None,
        qris_image: Optional[str] = None,
    ):
        """Update informasi pembayaran pesanan."""
        if payment_status == "paid":
            self.conn.execute(
                """UPDATE orders SET
                    payment_status = ?, payment_id = ?,
                    paid_at = CURRENT_TIMESTAMP,
                    status = 'paid',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (payment_status, payment_id, order_id),
            )
        else:
            self.conn.execute(
                """UPDATE orders SET
                    payment_status = ?, payment_id = ?,
                    payment_url = ?, qris_image = ?, qris_data = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?""",
                (payment_status, payment_id, qris_url, qris_image, qris_data, order_id),
            )
        self.conn.commit()

    def get_order_count_by_status(self) -> Dict[str, int]:
        """Dapatkan jumlah pesanan per status."""
        rows = self.conn.execute(
            "SELECT status, COUNT(*) as cnt FROM orders GROUP BY status"
        ).fetchall()
        return {r["status"]: r["cnt"] for r in rows}

    # =================================================================
    # Payments
    # =================================================================

    def create_payment(
        self,
        payment_id: str,
        order_id: str,
        user_id: int,
        amount: int,
        qris_url: str = "",
        qris_data: str = "",
        qris_image: str = "",
    ):
        """Catat pembayaran baru."""
        from datetime import timedelta

        expired_at = datetime.now(timezone.utc) + timedelta(minutes=30)

        self.conn.execute(
            """INSERT OR REPLACE INTO payments
               (id, order_id, user_id, amount, status, qris_url,
                qris_data, qris_image, expired_at)
            VALUES (?, ?, ?, ?, 'pending', ?, ?, ?, ?)""",
            (payment_id, order_id, user_id, amount, qris_url, qris_data, qris_image, expired_at),
        )
        self.conn.commit()

    def update_payment_status(self, payment_id: str, status: str):
        """Update status pembayaran."""
        sql = """UPDATE payments SET status = ? WHERE id = ?"""
        if status == "paid":
            sql = """UPDATE payments SET status = ?, paid_at = CURRENT_TIMESTAMP WHERE id = ?"""
        self.conn.execute(sql, (status, payment_id))
        self.conn.commit()

    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan data pembayaran."""
        row = self.conn.execute(
            "SELECT * FROM payments WHERE id = ?", (payment_id,)
        ).fetchone()
        return dict(row) if row else None

    def get_payment_by_order(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Dapatkan pembayaran berdasarkan order_id."""
        row = self.conn.execute(
            "SELECT * FROM payments WHERE order_id = ? ORDER BY created_at DESC LIMIT 1",
            (order_id,),
        ).fetchone()
        return dict(row) if row else None


# Singleton instance
_db_instance: Optional[Database] = None


def get_db(db_path: Optional[str] = None) -> Database:
    """Dapatkan instance database singleton."""
    global _db_instance
    if _db_instance is None:
        path = db_path or os.environ.get("DATABASE_PATH", "data/bot.db")
        _db_instance = Database(path)
    return _db_instance
