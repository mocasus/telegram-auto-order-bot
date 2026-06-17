"""KlikQRIS Payment API Wrapper.

Mendukung mode sandbox dan production untuk integrasi pembayaran QRIS.
"""

import httpx
import hashlib
import hmac
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class KlikQRISError(Exception):
    """Exception untuk error KlikQRIS API."""
    pass


class KlikQRIS:
    """Wrapper API KlikQRIS untuk pembayaran QRIS.

    API Endpoints:
        - POST /v1/qris/create — Buat QRIS baru
        - GET  /v1/qris/status/{order_id} — Cek status pembayaran
        - GET  /v1/qris/history?page=N — Riwayat transaksi
        - Webhook callback untuk notifikasi pembayaran

    Usage:
        klik = KlikQRIS(api_key="xxx", merchant_id="xxx", mode="sandbox")
        result = klik.create_qris(order_id="ORD-001", amount=25000, keterangan="Pembayaran")
        status = klik.check_status("ORD-001")
    """

    SANDBOX_BASE_URL = "https://api.klikqris.com"
    PRODUCTION_BASE_URL = "https://api.klikqris.com"

    def __init__(
        self,
        api_key: str,
        merchant_id: str,
        mode: str = "sandbox",
        timeout: int = 30,
    ):
        """Inisialisasi KlikQRIS client.

        Args:
            api_key: API key dari KlikQRIS
            merchant_id: ID merchant
            mode: "sandbox" atau "production"
            timeout: Request timeout dalam detik
        """
        self.api_key = api_key
        self.merchant_id = merchant_id
        self.mode = mode
        self.timeout = timeout

        if mode == "sandbox":
            self.base_url = self.SANDBOX_BASE_URL
            logger.info("KlikQRIS berjalan dalam mode SANDBOX")
        else:
            self.base_url = self.PRODUCTION_BASE_URL
            logger.info("KlikQRIS berjalan dalam mode PRODUCTION")

        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """HTTP client dengan header autentikasi."""
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

    async def close(self):
        """Tutup HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _generate_signature(self, payload: dict) -> str:
        """Generate signature untuk verifikasi webhook.

        Args:
            payload: Data payload yang diterima

        Returns:
            HMAC-SHA256 signature
        """
        data = json.dumps(payload, sort_keys=True)
        return hmac.new(
            self.api_key.encode(), data.encode(), hashlib.sha256
        ).hexdigest()

    async def create_qris(
        self,
        order_id: str,
        amount: int,
        keterangan: str = "",
    ) -> Dict[str, Any]:
        """Buat pembayaran QRIS baru.

        POST /v1/qris/create

        Args:
            order_id: ID pesanan unik
            amount: Jumlah pembayaran (Rupiah)
            keterangan: Deskripsi pembayaran

        Returns:
            Dict response API:
            {
                "status": "success",
                "data": {
                    "order_id": "...",
                    "qris_url": "...",
                    "qris_data": "...",
                    "qris_image": "...",
                    "amount": ...,
                    "expired_at": "..."
                }
            }

        Raises:
            KlikQRISError: Jika API request gagal
        """
        payload = {
            "order_id": order_id,
            "amount": amount,
            "id_merchant": self.merchant_id,
            "keterangan": keterangan,
        }

        logger.info(
            "Membuat QRIS: order_id=%s amount=%d mode=%s",
            order_id, amount, self.mode,
        )

        try:
            response = await self.client.post(
                f"{self.base_url}/v1/qris/create",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                raise KlikQRISError(
                    f"Gagal membuat QRIS: {data.get('message', 'Unknown error')}"
                )

            logger.info("QRIS berhasil dibuat: %s", order_id)
            return data

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error saat membuat QRIS: %s", e)
            raise KlikQRISError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Network error saat membuat QRIS: %s", e)
            raise KlikQRISError(f"Network error: {e}") from e

    async def check_status(self, order_id: str) -> Dict[str, Any]:
        """Cek status pembayaran QRIS.

        GET /v1/qris/status/{order_id}

        Args:
            order_id: ID pesanan

        Returns:
            Dict response API:
            {
                "status": "success",
                "data": {
                    "order_id": "...",
                    "payment_status": "pending|paid|expired|failed",
                    "amount": ...,
                    "paid_at": "..."
                }
            }
        """
        logger.debug("Cek status QRIS: %s", order_id)

        try:
            response = await self.client.get(
                f"{self.base_url}/v1/qris/status/{order_id}",
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") != "success":
                logger.warning("Status check gagal untuk %s: %s", order_id, data)
                return {"status": "error", "data": {"payment_status": "unknown"}}

            return data

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error saat cek status: %s", e)
            raise KlikQRISError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Network error saat cek status: %s", e)
            raise KlikQRISError(f"Network error: {e}") from e

    async def get_history(self, page: int = 1) -> Dict[str, Any]:
        """Dapatkan riwayat transaksi.

        GET /v1/qris/history?page=N

        Args:
            page: Nomor halaman

        Returns:
            Dict response API
        """
        logger.debug("Mengambil riwayat transaksi halaman %d", page)

        try:
            response = await self.client.get(
                f"{self.base_url}/v1/qris/history",
                params={"page": page},
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            logger.error("HTTP error saat ambil history: %s", e)
            raise KlikQRISError(f"HTTP error: {e.response.status_code}") from e
        except httpx.RequestError as e:
            logger.error("Network error saat ambil history: %s", e)
            raise KlikQRISError(f"Network error: {e}") from e

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Verifikasi signature webhook callback.

        Webhook callback dari KlikQRIS:
        POST dengan body JSON: {order_id, status (SUCCESS/EXPIRED), amount, ...}
        Header: x-signature

        Args:
            payload: JSON body yang diterima
            signature: Nilai header x-signature

        Returns:
            True jika signature valid
        """
        expected = self._generate_signature(payload)
        return hmac.compare_digest(expected, signature)

    async def parse_webhook(
        self, payload: dict, signature: str
    ) -> Optional[Dict[str, Any]]:
        """Parse dan verifikasi webhook callback.

        Args:
            payload: JSON body webhook
            signature: Header x-signature

        Returns:
            Dict yang sudah tervalidasi, atau None jika invalid

        Webhook payload format:
        {
            "order_id": "ORD-xxx",
            "status": "SUCCESS",  # atau "EXPIRED"
            "amount": 25000,
            "paid_at": "2024-01-01T00:00:00Z",
            "payment_method": "qris",
            "transaction_id": "TRX-xxx"
        }
        """
        if not self.verify_webhook(payload, signature):
            logger.warning("Webhook signature invalid untuk order: %s", payload.get("order_id"))
            return None

        order_id = payload.get("order_id")
        status = payload.get("status", "").upper()

        if status == "SUCCESS":
            payment_status = "paid"
        elif status == "EXPIRED":
            payment_status = "expired"
        else:
            payment_status = "pending"

        logger.info(
            "Webhook diterima: order_id=%s status=%s amount=%s",
            order_id, status, payload.get("amount"),
        )

        return {
            "order_id": order_id,
            "status": payment_status,
            "amount": payload.get("amount"),
            "paid_at": payload.get("paid_at"),
            "payment_method": payload.get("payment_method", "qris"),
            "transaction_id": payload.get("transaction_id"),
            "raw": payload,
        }


# ============================================================
# Helper untuk format uang Rupiah
# ============================================================

def format_rupiah(amount: int) -> str:
    """Format angka ke string Rupiah.

    Args:
        amount: Jumlah dalam Rupiah

    Returns:
        String terformat, e.g. "Rp 25.000"
    """
    if amount >= 0:
        return f"Rp {amount:,.0f}".replace(",", ".")
    else:
        return f"-Rp {abs(amount):,.0f}".replace(",", ".")


def generate_order_id(user_id: int) -> str:
    """Generate order ID unik.

    Format: ORD-YYYYMMDD-HHMMSS-USERID-RANDOM

    Args:
        user_id: ID user Telegram

    Returns:
        String order ID
    """
    import random
    import string

    now = datetime.now(timezone.utc)
    ts = now.strftime("%Y%m%d-%H%M%S")
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{ts}-{user_id}-{rand}"
