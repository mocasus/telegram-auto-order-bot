"""SQLite database layer for Simpel Order Bot.

Uses Python stdlib sqlite3 only (no ORM). Module-level connection `_conn`
is initialized by `init_db()`. All query helpers return plain `dict`s
(via `_row_to_dict`) so handlers can read fields by name. `sqlite3.Error`
exceptions are intentionally NOT caught here — handlers decide how to
react.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

# Module-level connection. `None` until `init_db()` is called.
_conn: sqlite3.Connection | None = None


# Schema lives as a single script string so `executescript()` can build all
# three tables in one shot. Order of statements matters for the FK from
# `orders.product_id` -> `products.id`, so `products` must come first.
_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  price INTEGER NOT NULL,
  description TEXT DEFAULT '',
  created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
  id TEXT PRIMARY KEY,
  user_id INTEGER NOT NULL,
  username TEXT,
  first_name TEXT,
  product_id INTEGER NOT NULL,
  quantity INTEGER NOT NULL,
  total INTEGER NOT NULL,
  status TEXT DEFAULT 'pending',
  qris_ref TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  FOREIGN KEY (product_id) REFERENCES products(id)
);

CREATE TABLE IF NOT EXISTS users (
  user_id INTEGER PRIMARY KEY,
  username TEXT,
  first_name TEXT,
  last_seen TEXT DEFAULT (datetime('now'))
);
"""


def _row_to_dict(row: sqlite3.Row | None) -> dict | None:
    """Convert a sqlite3.Row into a plain dict. `None` stays `None`."""
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def init_db(path: str) -> None:
    """Initialize the database at `path` and create tables if missing.

    - Creates the parent directory tree.
    - Opens a connection with `check_same_thread=False` (Telegram's
      async runtime may call into us from multiple threads).
    - Sets `row_factory = sqlite3.Row` so helpers can use `_row_to_dict`.
    - Runs the schema script and commits.
    """
    global _conn

    Path(path).parent.mkdir(parents=True, exist_ok=True)

    _conn = sqlite3.connect(str(path), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.executescript(_SCHEMA_SQL)
    # Idempotent migration: tambah kolom qris_ref ke orders jika DB lama.
    try:
        _conn.execute("ALTER TABLE orders ADD COLUMN qris_ref TEXT")
        _conn.commit()
    except sqlite3.OperationalError:
        pass  # kolom sudah ada
    _conn.commit()


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------


def add_product(name: str, price: int, description: str) -> int:
    """Insert a new product and return its `lastrowid`."""
    assert _conn is not None, "init_db() must be called before add_product()"
    cur = _conn.execute(
        "INSERT INTO products (name, price, description) VALUES (?, ?, ?)",
        (name, price, description),
    )
    _conn.commit()
    # `lastrowid` is always set for an INSERT into a ROWID table.
    assert cur.lastrowid is not None
    return cur.lastrowid


def list_products() -> list[dict]:
    """Return all products as a list of dicts, ordered by id."""
    assert _conn is not None, "init_db() must be called before list_products()"
    rows = _conn.execute("SELECT * FROM products ORDER BY id ASC").fetchall()
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def get_product(pid: int) -> dict | None:
    """Return a single product dict by id, or `None` if not found."""
    assert _conn is not None, "init_db() must be called before get_product()"
    row = _conn.execute("SELECT * FROM products WHERE id = ?", (pid,)).fetchone()
    return _row_to_dict(row)  # type: ignore[return-value]


def delete_product(pid: int) -> bool:
    """Delete the product with the given id. Returns True if a row was removed."""
    assert _conn is not None, "init_db() must be called before delete_product()"
    cur = _conn.execute("DELETE FROM products WHERE id = ?", (pid,))
    _conn.commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------


def create_order(
    order_id: str,
    user_id: int,
    username: str | None,
    first_name: str | None,
    product_id: int,
    quantity: int,
    total: int,
    qris_ref: str | None = None,
) -> None:
    """Insert a new order. The `status` defaults to 'pending' via the schema.

    `qris_ref` diisi dengan ID referensi KlikQRIS (biasanya = order_id) setelah
    QRIS berhasil dibuat. None = order manual transfer.
    """
    assert _conn is not None, "init_db() must be called before create_order()"
    _conn.execute(
        """
        INSERT INTO orders
            (id, user_id, username, first_name, product_id, quantity, total, qris_ref)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (order_id, user_id, username, first_name, product_id, quantity, total, qris_ref),
    )
    _conn.commit()


def get_user_orders(user_id: int) -> list[dict]:
    """Return all orders for `user_id`, newest first."""
    assert _conn is not None, "init_db() must be called before get_user_orders()"
    rows = _conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def get_all_orders(limit: int = 50, status: str | None = None) -> list[dict]:
    """Return recent orders, newest first. Optionally filtered by `status`."""
    assert _conn is not None, "init_db() must be called before get_all_orders()"
    if status is None:
        rows = _conn.execute(
            "SELECT * FROM orders ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    else:
        rows = _conn.execute(
            "SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC LIMIT ?",
            (status, limit),
        ).fetchall()
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


def update_order_status(order_id: str, status: str) -> bool:
    """Set the status of an order. Returns True if a row was updated."""
    assert _conn is not None, "init_db() must be called before update_order_status()"
    cur = _conn.execute(
        "UPDATE orders SET status = ? WHERE id = ?",
        (status, order_id),
    )
    _conn.commit()
    return cur.rowcount > 0


def set_order_qris_ref(order_id: str, qris_ref: str) -> bool:
    """Set qris_ref untuk order yang sudah berhasil dibuat QRIS-nya."""
    assert _conn is not None, "init_db() must be called before set_order_qris_ref()"
    cur = _conn.execute(
        "UPDATE orders SET qris_ref = ? WHERE id = ?",
        (qris_ref, order_id),
    )
    _conn.commit()
    return cur.rowcount > 0


def get_pending_qris_orders() -> list[dict]:
    """Ambil semua order pending yang punya qris_ref (untuk di-poll)."""
    assert _conn is not None, "init_db() must be called before get_pending_qris_orders()"
    rows = _conn.execute(
        "SELECT * FROM orders WHERE status = 'pending' AND qris_ref IS NOT NULL ORDER BY created_at ASC LIMIT 50"
    ).fetchall()
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


def upsert_user(user_id: int, username: str | None, first_name: str | None) -> None:
    """Insert or replace a user row, refreshing `last_seen` to now."""
    assert _conn is not None, "init_db() must be called before upsert_user()"
    _conn.execute(
        """
        INSERT OR REPLACE INTO users (user_id, username, first_name, last_seen)
        VALUES (?, ?, ?, datetime('now'))
        """,
        (user_id, username, first_name),
    )
    _conn.commit()


def get_all_user_ids() -> list[int]:
    """Return a list of all known Telegram user_ids (for broadcast)."""
    assert _conn is not None, "init_db() must be called before get_all_user_ids()"
    rows = _conn.execute("SELECT user_id FROM users").fetchall()
    return [int(row["user_id"]) for row in rows]
