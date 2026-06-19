# 🤖 Telegram Auto Order Bot

<p align="center">
  <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/logo.svg" alt="Logo" width="160">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License">
  <a href="https://t.me/mmocaauto_bot"><img src="https://img.shields.io/badge/Demo-@mmocaauto_bot-2CA5E0?style=flat-square&logo=telegram&logoColor=white" alt="Demo"></a>
</p>

---

<details open>
<summary><strong>🇮🇩 Bahasa Indonesia</strong></summary>

<br>

### Daftar Isi
- [Tentang](#tentang)
- [Fitur](#fitur)
- [Mulai Cepat](#mulai-cepat)
- [Konfigurasi](#konfigurasi)
- [Pembayaran (KlikQRIS)](#pembayaran-klikqris)
- [Cara Kerja](#cara-kerja)
- [Penggunaan](#penggunaan)
- [Tech Stack](#tech-stack)
- [Struktur Proyek](#struktur-proyek)
- [Deploy](#deploy)
- [Roadmap](#roadmap)
- [Lisensi](#lisensi)

### Tentang
Bot Telegram buat jualan online. User lihat katalog, order, dapat info rekening atau QRIS. Admin tambah produk & ubah status order. Pakai SQLite, jalan di VPS kecil.

Cocok buat: toko kecil, reseller, jualan pribadi, testing, demo.

### Fitur
- 🛍️ Katalog produk via inline keyboard
- 🛒 Order 3 langkah: pilih → jumlah → konfirmasi
- 💳 Pembayaran QRIS via KlikQRIS (auto QR + auto-verify)
- ⏰ Auto-cancel order kadaluarsa / gagal bayar
- 📋 Riwayat order per user (`/myorders`)
- 🔧 Admin: tambah/hapus produk, lihat order, ubah status, broadcast
- 🗄️ SQLite single-file, tanpa setup DB server
- 🚀 Deps minimal: 2 package (PTB + dotenv)

### Mulai Cepat
```bash
git clone https://github.com/mocasus/telegram-auto-order-bot.git
cd telegram-auto-order-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # isi TELEGRAM_BOT_TOKEN, ADMIN_USER_ID, info rekening
python bot.py
```

Butuh: Python 3.11+, token dari [@BotFather](https://t.me/BotFather), user ID admin dari [@userinfobot](https://t.me/userinfobot).

### Konfigurasi
Semua via `.env`:

| Var | Wajib | Default | Keterangan |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | ya | — | Token dari @BotFather |
| `ADMIN_USER_ID` | ya | — | User ID admin Telegram |
| `PAYMENT_BANK` | tidak | `BCA` | Nama bank / e-wallet |
| `PAYMENT_NUMBER` | tidak | `123-456-789` | Nomor rekening |
| `PAYMENT_NAME` | tidak | `Moca` | Atas nama |
| `SHOP_NAME` | tidak | `Toko Moca` | Nama toko |
| `DB_PATH` | tidak | `data/bot.db` | Lokasi database |
| `KLIKQRIS_API_KEY` | tidak | — | API key dari [KlikQRIS](https://klikqris.com) |
| `KLIKQRIS_MERCHANT_ID` | tidak | — | Merchant ID KlikQRIS |
| `KLIKQRIS_MODE` | tidak | `sandbox` | `sandbox` (testing) atau `production` |

Isi 3 var KlikQRIS di atas untuk auto-generate QR di tiap order + auto-verify pembayaran. Kosongkan untuk fallback ke info transfer manual (admin verify sendiri).

### Pembayaran (KlikQRIS)
1. Daftar gratis di [klikqris.com](https://klikqris.com) (ada mode sandbox untuk testing tanpa uang sungguhan).
2. Login dashboard → ambil **API Key** + **Merchant ID**.
3. Isi ke `.env`, set `KLIKQRIS_MODE=sandbox` dulu untuk coba-coba.
4. Ganti ke `production` kalau udah siap terima uang beneran.

Flow: user order → bot generate QR → user scan & bayar → poller (tiap 10 detik) cek status → kalau sukses, order auto `paid` + user dapat notif. Expired/failed → auto `cancelled`.

### Cara Kerja
1. User `/katalog` → bot ambil produk dari DB
2. User klik Beli → masukkan jumlah → klik Konfirmasi
3. Bot panggil KlikQRIS `create_qris(order_id, total)` → dapat URL QR
4. Bot kirim foto QR + detail order ke user
5. User scan & bayar via app bank/e-wallet
6. Poller (tiap 10 detik) panggil `check_status(order_id)`
7. Status `paid` → update DB, notif user & admin
8. Status `expired`/`failed` → update DB, notif user

Kalau KlikQRIS non-aktif, step 3-4 diganti tampil info rekening manual. Admin verify sendiri di `/orders`.

### Penggunaan

**User:**

| Command | Fungsi |
|---|---|
| `/start` | Menu utama |
| `/katalog` | Lihat produk & order |
| `/myorders` | Lihat orderan kamu |
| `/help` | Bantuan |

Cara order: klik produk di katalog → masukkan jumlah → klik Konfirmasi. Bot kasih nomor order & info rekening.

**Admin** (user ID sesuai `ADMIN_USER_ID`):

| Command | Fungsi |
|---|---|
| `/addproduct` | Tambah produk (nama, harga, deskripsi) |
| `/listproducts` | Daftar semua produk |
| `/delproduct <id>` | Hapus produk |
| `/orders` | Lihat order + ubah status (Paid / Cancel) |
| `/broadcast <pesan>` | Kirim pesan ke semua user |

### Tech Stack
| Komponen | Kenapa |
|---|---|
| Python 3.11 | Async bawaan, syntax modern |
| python-telegram-bot v22 | Library resmi Telegram, async, stabil |
| SQLite (stdlib) | Single file, tanpa server, cukup ribuan order |
| KlikQRIS | QRIS langsung, murah, support sandbox |
| python-dotenv | Config via `.env`, simple |

### Struktur Proyek
```
telegram-auto-order-bot/
├── bot.py              # entry point
├── config.py           # load .env
├── db.py               # helper SQLite
├── payments/
│   └── klikqris.py     # client KlikQRIS API
├── jobs/
│   └── poller.py       # background QRIS status checker
├── handlers/
│   ├── start.py        # /start, /help
│   ├── product.py      # /katalog + order flow
│   ├── myorders.py     # /myorders
│   └── admin.py        # /addproduct, /orders, dll
├── .env.example
├── requirements.txt
├── SPEC.md             # spek teknis lengkap
└── README.md
```

### Deploy (systemd, VPS Linux)
```bash
sudo cp -r . /opt/telegram-auto-order-bot/
cd /opt/telegram-auto-order-bot
python3 -m venv venv && venv/bin/pip install -r requirements.txt
sudo cp telegram-auto-order-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-auto-order-bot
sudo journalctl -u telegram-auto-order-bot -f
```

File `telegram-auto-order-bot.service` ada di repo. Edit `User=` dan `Documentation=` sesuai setup lo.

### Roadmap
- [ ] Multi-admin
- [ ] Kategori produk
- [ ] Export order ke Excel/CSV
- [ ] Notifikasi admin tiap order masuk
- [ ] Webhook KlikQRIS (selain polling)
- [ ] Keranjang (opsional, toggle)

### Lisensi
MIT. Lihat [LICENSE](LICENSE).

</details>

---

<details>
<summary><strong>🇬🇧 English</strong></summary>

<br>

### Table of Contents
- [About](#about)
- [Features](#features)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Payment (KlikQRIS)](#payment-klikqris)
- [How It Works](#how-it-works)
- [Usage](#usage)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Deploy](#deploy-1)
- [Roadmap](#roadmap)
- [License](#license)

### About
Telegram bot for running a small shop. Users browse the catalog, place orders, and get bank transfer info or a QRIS code. Admin adds products and updates order status. SQLite under the hood, runs on a small VPS.

Good for: small shops, resellers, personal selling, testing, demos.

### Features
- 🛍️ Product catalog via inline keyboard
- 🛒 3-step order: pick → quantity → confirm
- 💳 QRIS payment via KlikQRIS (auto QR + auto-verify)
- ⏰ Auto-cancel expired / failed orders
- 📋 Per-user order history (`/myorders`)
- 🔧 Admin: add/remove products, view orders, change status, broadcast
- 🗄️ SQLite single-file, no DB server needed
- 🚀 Minimal deps: 2 packages (PTB + dotenv)

### Quick Start
```bash
git clone https://github.com/mocasus/telegram-auto-order-bot.git
cd telegram-auto-order-bot
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env   # fill TELEGRAM_BOT_TOKEN, ADMIN_USER_ID, bank info
python bot.py
```

Requires: Python 3.11+, token from [@BotFather](https://t.me/BotFather), admin user ID from [@userinfobot](https://t.me/userinfobot).

### Configuration
All via `.env`:

| Var | Required | Default | Description |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | yes | — | Token from @BotFather |
| `ADMIN_USER_ID` | yes | — | Telegram admin user ID |
| `PAYMENT_BANK` | no | `BCA` | Bank / e-wallet name |
| `PAYMENT_NUMBER` | no | `123-456-789` | Account number |
| `PAYMENT_NAME` | no | `Moca` | Account holder |
| `SHOP_NAME` | no | `Toko Moca` | Shop name |
| `DB_PATH` | no | `data/bot.db` | Database location |
| `KLIKQRIS_API_KEY` | no | — | API key from [KlikQRIS](https://klikqris.com) |
| `KLIKQRIS_MERCHANT_ID` | no | — | KlikQRIS merchant ID |
| `KLIKQRIS_MODE` | no | `sandbox` | `sandbox` (testing) or `production` |

Fill the 3 KlikQRIS vars above to auto-generate a QR for each order + auto-verify payment. Leave empty to fall back to manual bank transfer info (admin verifies by hand).

### Payment (KlikQRIS)
1. Sign up free at [klikqris.com](https://klikqris.com) (sandbox mode available for testing without real money).
2. Dashboard → grab **API Key** + **Merchant ID**.
3. Put them in `.env`, set `KLIKQRIS_MODE=sandbox` first to try things out.
4. Switch to `production` when you're ready to accept real payments.

Flow: user orders → bot generates QR → user scans & pays → poller (every 10s) checks status → on success, order auto-marked `paid` + user notified. Expired/failed → auto `cancelled`.

### How It Works
1. User `/katalog` → bot fetches products from DB
2. User clicks Buy → enters quantity → clicks Confirm
3. Bot calls KlikQRIS `create_qris(order_id, total)` → gets QR URL
4. Bot sends QR photo + order details to user
5. User scans & pays via bank/e-wallet app
6. Poller (every 10s) calls `check_status(order_id)`
7. Status `paid` → update DB, notify user & admin
8. Status `expired`/`failed` → update DB, notify user

When KlikQRIS is inactive, steps 3-4 are replaced with manual bank info. Admin verifies manually in `/orders`.

### Usage

**User:**

| Command | Action |
|---|---|
| `/start` | Main menu |
| `/katalog` | Browse & order products |
| `/myorders` | Your orders |
| `/help` | Help |

Order flow: click a product in the catalog → enter quantity → click Confirm. The bot replies with the order ID and bank details.

**Admin** (user ID matches `ADMIN_USER_ID`):

| Command | Action |
|---|---|
| `/addproduct` | Add product (name, price, description) |
| `/listproducts` | List all products |
| `/delproduct <id>` | Delete a product |
| `/orders` | View orders + change status (Paid / Cancel) |
| `/broadcast <message>` | Send a message to all users |

### Tech Stack
| Component | Why |
|---|---|
| Python 3.11 | Built-in async, modern syntax |
| python-telegram-bot v22 | Official Telegram library, async, stable |
| SQLite (stdlib) | Single file, no server, handles thousands of orders |
| KlikQRIS | Direct QRIS, cheap, supports sandbox |
| python-dotenv | Config via `.env`, simple |

### Project Structure
```
telegram-auto-order-bot/
├── bot.py              # entry point
├── config.py           # load .env
├── db.py               # SQLite helper
├── payments/
│   └── klikqris.py     # KlikQRIS API client
├── jobs/
│   └── poller.py       # background QRIS status checker
├── handlers/
│   ├── start.py        # /start, /help
│   ├── product.py      # /katalog + order flow
│   ├── myorders.py     # /myorders
│   └── admin.py        # /addproduct, /orders, etc.
├── .env.example
├── requirements.txt
├── SPEC.md             # full technical spec
└── README.md
```

### Deploy (systemd, Linux VPS)
```bash
sudo cp -r . /opt/telegram-auto-order-bot/
cd /opt/telegram-auto-order-bot
python3 -m venv venv && venv/bin/pip install -r requirements.txt
sudo cp telegram-auto-order-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-auto-order-bot
sudo journalctl -u telegram-auto-order-bot -f
```

File `telegram-auto-order-bot.service` is included. Edit `User=` and `Documentation=` for your setup.

### Roadmap
- [ ] Multi-admin
- [ ] Product categories
- [ ] Export orders to Excel/CSV
- [ ] Admin notification per new order
- [ ] KlikQRIS webhook (in addition to polling)
- [ ] Shopping cart (optional, toggle)

### License
MIT. See [LICENSE](LICENSE).

</details>

---

## 🔗 Links
- 📦 Repo: [github.com/mocasus/telegram-auto-order-bot](https://github.com/mocasus/telegram-auto-order-bot)
- 🤖 Demo: [@mmocaauto_bot](https://t.me/mmocaauto_bot)
