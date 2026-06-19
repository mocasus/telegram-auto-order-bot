"""KlikQRIS payment gateway client.

Mendukung mode sandbox & production. API base: https://api.klikqris.com

Module-level singleton: `init()` dipanggil dari bot.py, lalu `get()`
mengembalikan instance yang siap pakai. `is_active()` menandakan apakah
kredensial terkonfigurasi (jika tidak, bot fallback ke info transfer manual).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


class KlikQRISError(Exception):
    """Exception untuk error KlikQRIS API."""


class KlikQRIS:
    """Wrapper API KlikQRIS untuk pembayaran QRIS.

    Endpoints:
        - POST /v1/qris/create
        - GET  /v1/qris/status/{order_id}
    """

    BASE_URL = "https://api.klikqris.com"

    def __init__(self, api_key: str, merchant_id: str, mode: str = "sandbox", timeout: int = 30):
        self.api_key = api_key
        self.merchant_id = merchant_id
        self.mode = mode
        self.timeout = timeout
        self.base_url = self.BASE_URL
        self._client: Optional[httpx.AsyncClient] = None
        logger.info("KlikQRIS mode: %s", mode)

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "x-api-key": self.api_key,
                    "id_merchant": self.merchant_id,
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def create_qris(self, order_id: str, amount: int, keterangan: str = "") -> dict[str, Any]:
        """Buat QRIS baru. Return dict { data: { qris_image, qris_data, amount, expired_at, ... } }."""
        payload = {
            "order_id": order_id,
            "amount": amount,
            "id_merchant": self.merchant_id,
            "keterangan": keterangan,
        }
        logger.info("Create QRIS: %s amount=%d mode=%s", order_id, amount, self.mode)
        try:
            r = await self.client.post(f"{self.base_url}/v1/qris/create", json=payload)
            r.raise_for_status()
            data = r.json()
            if data.get("status") != "success":
                raise KlikQRISError(data.get("message", "Unknown error"))
            return data
        except httpx.HTTPStatusError as e:
            raise KlikQRISError(f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise KlikQRISError(f"Network error: {e}") from e

    async def check_status(self, order_id: str) -> dict[str, Any]:
        """Cek status QRIS. Return { data: { payment_status, ... } }."""
        try:
            r = await self.client.get(f"{self.base_url}/v1/qris/status/{order_id}")
            r.raise_for_status()
            data = r.json()
            if data.get("status") != "success":
                return {"status": "error", "data": {"payment_status": "unknown"}}
            return data
        except httpx.HTTPStatusError as e:
            raise KlikQRISError(f"HTTP {e.response.status_code}") from e
        except httpx.RequestError as e:
            raise KlikQRISError(f"Network error: {e}") from e

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        data = json.dumps(payload, sort_keys=True)
        expected = hmac.new(self.api_key.encode(), data.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


# Module-level singleton
_client: Optional[KlikQRIS] = None


def init(api_key: str, merchant_id: str, mode: str = "sandbox", timeout: int = 30) -> KlikQRIS:
    """Inisialisasi singleton. Dipanggil sekali dari bot.py."""
    global _client
    _client = KlikQRIS(api_key=api_key, merchant_id=merchant_id, mode=mode, timeout=timeout)
    return _client


def get() -> KlikQRIS:
    """Ambil instance. Raise RuntimeError jika belum init."""
    if _client is None:
        raise RuntimeError("KlikQRIS belum diinisialisasi. Panggil klikqris.init() dulu.")
    return _client


def is_active() -> bool:
    """True jika kredensial terpasang dan singleton sudah di-init."""
    return _client is not None


async def shutdown() -> None:
    """Tutup HTTP client saat bot shutdown."""
    global _client
    if _client:
        await _client.close()
        _client = None
