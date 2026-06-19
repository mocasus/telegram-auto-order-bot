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
- [Mulai Cepat](#mulai-cepat)
- [Konfigurasi](#konfigurasi)
- [Penggunaan](#penggunaan)
- [Struktur Proyek](#struktur-proyek)
- [Deploy](#deploy)
- [Lisensi](#lisensi)

### Tentang
Bot Telegram buat jualan online. User lihat katalog, order, dapat info rekening. Admin tambah produk & ubah status order. Pakai SQLite, jalan di VPS kecil.

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

### Struktur Proyek
```
telegram-auto-order-bot/
├── bot.py              # entry point
├── config.py           # load .env
├── db.py               # helper SQLite
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

### Lisensi
MIT. Lihat [LICENSE](LICENSE).

</details>

---

<details>
<summary><strong>🇬🇧 English</strong></summary>

<br>

### Table of Contents
- [About](#about)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Deploy](#deploy-1)
- [License](#license)

### About
Telegram bot for running a small shop. Users browse the catalog, place orders, and get bank transfer info. Admin adds products and marks orders as paid. SQLite under the hood, runs on a small VPS.

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

### Project Structure
```
telegram-auto-order-bot/
├── bot.py              # entry point
├── config.py           # load .env
├── db.py               # SQLite helper
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

### License
MIT. See [LICENSE](LICENSE).

</details>

---

## 🔗 Links
- 📦 Repo: [github.com/mocasus/telegram-auto-order-bot](https://github.com/mocasus/telegram-auto-order-bot)
- 🤖 Demo: [@mmocaauto_bot](https://t.me/mmocaauto_bot)
