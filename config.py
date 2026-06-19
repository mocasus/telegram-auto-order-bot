"""Load .env dan expose konstanta konfigurasi bot."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env di folder yang sama dengan file ini.
load_dotenv(dotenv_path=Path(__file__).parent / ".env")


def _require_env(key: str) -> str:
    """Ambil env var; raise SystemExit jika kosong."""
    value = os.getenv(key, "").strip()
    if not value:
        raise SystemExit(f"{key} tidak ditemukan di .env")
    return value


def _require_int_env(key: str) -> int:
    """Ambil env var dan cast ke int; raise SystemExit jika kosong/invalid."""
    raw = os.getenv(key, "").strip()
    if not raw:
        raise SystemExit(f"{key} tidak ditemukan di .env")
    try:
        return int(raw)
    except ValueError:
        raise SystemExit(f"{key} harus berupa angka integer yang valid di .env")


BOT_TOKEN: str = _require_env("TELEGRAM_BOT_TOKEN")
ADMIN_USER_ID: int = _require_int_env("ADMIN_USER_ID")

PAYMENT_BANK: str = os.getenv("PAYMENT_BANK", "BCA")
PAYMENT_NUMBER: str = os.getenv("PAYMENT_NUMBER", "123-456-789")
PAYMENT_NAME: str = os.getenv("PAYMENT_NAME", "Moca")
SHOP_NAME: str = os.getenv("SHOP_NAME", "Toko Moca")
DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")
