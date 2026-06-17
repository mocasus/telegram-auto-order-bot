# 🤖 Telegram Auto Order Bot

<p align="center">
  <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/logo.svg" alt="Logo" width="200">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/PTB-v22+-2CA5E0?style=for-the-badge&logo=telegram" alt="PTB">
  <img src="https://img.shields.io/badge/Status-Active-brightgreen?style=for-the-badge" alt="Status">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Database-SQLite_|_PostgreSQL-003B57?style=flat-square&logo=sqlite&logoColor=white" alt="Database">
  <img src="https://img.shields.io/badge/Deploy-systemd_|_PM2_|_Docker_|_Railway_|_Render-FF6C37?style=flat-square&logo=docker&logoColor=white" alt="Deploy">
  <img src="https://img.shields.io/badge/Payment-KlikQRIS_QRIS-0066AE?style=flat-square" alt="Payment">
</p>

---

## 🌐 Pilih Bahasa · Choose Language

<details open>
<summary><strong>🇮🇩 Bahasa Indonesia</strong></summary>

<br>

> Bot Telegram lengkap untuk katalog produk, keranjang belanja, checkout, dan pembayaran QRIS — semuanya dari dalam Telegram.

---

### 🚀 Mulai Cepat — 3 Langkah

**1. Clone repo**
```bash
git clone https://github.com/mocasus/telegram-auto-order-bot.git
cd telegram-auto-order-bot
```

**2. Setup konfigurasi**
```bash
cp .env.example .env
nano .env   # isi token bot & API key
```

**3. Jalankan**
```bash
pip install -r requirements.txt
python bot.py
```

✅ Bot langsung berjalan dengan **SQLite** (zero-config).

#### Prasyarat Minimal

| Kebutuhan | Detail |
|---|---|
| Python 3.11+ | [python.org](https://python.org) |
| Token Bot Telegram | dari [@BotFather](https://t.me/BotFather) |
| Akun KlikQRIS | API Key + Merchant ID |

---

### ✨ Fitur

| Fitur | Deskripsi |
|---|---|
| 🛍️ **Katalog Produk** | Jelajahi produk berdasarkan kategori dengan navigasi inline keyboard |
| 🛒 **Keranjang Belanja** | Tambah, hapus, atur jumlah, dan kosongkan keranjang |
| 💳 **Checkout QRIS** | Generate kode QRIS untuk pembayaran + verifikasi otomatis |
| 📦 **Riwayat Pesanan** | Lihat semua pesanan dan statusnya |
| ⚙️ **Panel Admin** | Dashboard admin: kelola produk, pesanan, ringkasan toko |
| 🔔 **Notifikasi Otomatis** | Polling 10-detik + webhook callback untuk status pembayaran |
| ⏱️ **Batas Waktu 30 Menit** | Pesanan otomatis dibatalkan jika tidak dibayar |
| 🔐 **Mode Sandbox** | Uji coba tanpa uang sungguhan |

---

### 🗄️ Pilihan Database

| Fitur | SQLite | PostgreSQL |
|---|---|---|
| Konfigurasi | Zero-config, langsung pakai | Perlu install & setup |
| Skalabilitas | Single-server, ringan | Multi-connection, production-ready |
| Cocok untuk | Development, bot kecil-menengah | Production, high-traffic |
| Setup | `database.path: "data/bot.db"` | `DATABASE_URL=postgresql://...` |

---

### 🖥️ Opsi Deploy

#### Perbandingan

| Metode | Tingkat Kesulitan | Biaya | Auto-restart | Cocok untuk |
|---|---|---|---|---|
| **PM2** | ⭐ Mudah | Gratis | ✅ | VPS kecil |
| **systemd** | ⭐⭐ Menengah | Gratis | ✅ | VPS/Linux server |
| **Docker** | ⭐⭐ Menengah | Gratis | ✅ | Any platform |
| **Railway** | ⭐ Mudah | Mulai ~$5/bln | ✅ | Zero-ops deploy |
| **Render** | ⭐ Mudah | Mulai gratis | ✅ | Zero-ops deploy |

---

#### 🟢 PM2 (Termudah)

```bash
# 1. Install PM2
npm install -g pm2

# 2. Jalankan bot
pm2 start bot.py --name "telegram-bot" --interpreter python3

# 3. Auto-start saat reboot
pm2 save
pm2 startup

# Monitoring
pm2 status
pm2 logs telegram-bot
```

> PM2 adalah process manager Node.js yang juga bisa menjalankan Python. Paling sederhana untuk VPS kecil.

---

#### 🔵 systemd (Linux Server)

```bash
# 1. Setup direktori aplikasi
sudo mkdir -p /opt/telegram-auto-order-bot
sudo cp -r . /opt/telegram-auto-order-bot/
cd /opt/telegram-auto-order-bot

# 2. Buat virtualenv & install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Konfigurasi
cp .env.example .env && nano .env

# 4. Install & jalankan service
sudo cp telegram-auto-order-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-auto-order-bot

# Monitoring
sudo systemctl status telegram-auto-order-bot
sudo journalctl -u telegram-auto-order-bot -f
```

> Opsi terbaik untuk VPS Linux. Terintegrasi penuh dengan sistem operasi, auto-restart, dan logging ke journald.

---

#### 🐳 Docker

```bash
# Docker Compose (direkomendasikan)
cp .env.example .env && nano .env
docker compose up -d

# Monitoring
docker compose logs -f bot
```

<details>
<summary>Docker Run (manual)</summary>

```bash
docker build -t telegram-auto-order-bot .
docker run -d \
  --name telegram-auto-order-bot \
  --env-file .env \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  telegram-auto-order-bot
```
</details>

---

#### 🚂 Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new)

> Deploy instan ke Railway. Platform-as-a-Service dengan auto-deploy dari GitHub, logging, dan environment variables UI.

```bash
# 1. Fork/clone repo ini ke GitHub Anda
# 2. Klik tombol "Deploy on Railway" di atas
# 3. Isi environment variables di dashboard Railway
# 4. Done! Bot langsung berjalan
```

**railway.json** (opsional, untuk konfigurasi deploy):
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python bot.py",
    "healthcheckPath": "/",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

#### ⚡ Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

> Deploy gratis ke Render dengan free tier. Mendukung background worker untuk bot Telegram.

**render.yaml**:
```yaml
services:
  - type: worker
    name: telegram-auto-order-bot
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: KLIKQRIS_API_KEY
        sync: false
      - key: KLIKQRIS_MERCHANT_ID
        sync: false
      - key: KLIKQRIS_MODE
        value: sandbox
      - key: ADMIN_USER_ID
        sync: false
```

---

### 🔧 Konfigurasi Lengkap

#### `.env` — Environment Variables

| Variable | Deskripsi | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token bot dari @BotFather | *(wajib)* |
| `KLIKQRIS_API_KEY` | API Key KlikQRIS | *(wajib)* |
| `KLIKQRIS_MERCHANT_ID` | Merchant ID | *(wajib)* |
| `KLIKQRIS_MODE` | `sandbox` atau `production` | `sandbox` |
| `ADMIN_USER_ID` | User ID admin Telegram | *(wajib)* |
| `DATABASE_URL` | URL PostgreSQL (opsional) | *(SQLite default)* |
| `WEBHOOK_URL` | URL webhook callback | *(kosong)* |
| `CONFIG_PATH` | Path ke config.yaml | `config.yaml` |

#### `config.yaml` — Semua Opsi

```yaml
bot:
  token: "TOKEN_BOT"          # Token dari @BotFather
  name: "NamaBot"             # Nama tampilan
  username: "UsernameBot"     # Username bot (tanpa @)

klikqris:
  api_key: "API_KEY"          # API Key KlikQRIS
  merchant_id: "MERCHANT_ID"  # Merchant ID
  mode: sandbox               # sandbox | production
  timeout: 30                 # Request timeout (detik)
  polling_interval: 10        # Interval cek status (detik)
  max_polling_attempts: 30    # Maks polling sebelum expired

database:
  path: "data/bot.db"         # Path file SQLite (abaikan jika pakai PostgreSQL)
  url: ""                     # PostgreSQL URL (opsional): postgresql://user:pass@host/db

webhook:
  enabled: false              # true = webhook, false = polling
  url: "https://..."          # URL webhook (HTTPS required)
  port: 8443                  # Port webhook server

admin:
  user_id: 123456789          # User ID admin utama
  additional_ids: []          # Admin tambahan

toko:
  name: "Toko Online"         # Nama toko
  currency: "IDR"             # Mata uang
  currency_symbol: "Rp"       # Simbol
  admin_fee: 0                # Biaya admin per transaksi
  tax_percent: 0              # PPN (persentase)
```

---

### 🔌 KlikQRIS API

#### Endpoints

| Method | Endpoint | Deskripsi |
|---|---|---|
| `POST` | `/v1/qris/create` | Buat pembayaran QRIS baru |
| `GET` | `/v1/qris/status/{order_id}` | Cek status pembayaran |
| `GET` | `/v1/qris/history?page=N` | Riwayat transaksi |
| `POST` | Webhook Callback | Notifikasi pembayaran |

> **Mode Sandbox:** Gunakan `KLIKQRIS_MODE=sandbox` untuk testing tanpa uang sungguhan.

---

### 🎮 Penggunaan

#### Perintah Bot

| Command | Fungsi |
|---|---|
| `/start` | Menu utama dengan tombol inline |
| `/bantuan` | Pusat bantuan |
| `/menu` | Kembali ke menu utama |
| `/cancel` | Batalkan operasi yang sedang berjalan |

#### Alur Belanja

<p align="center">
  <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/flow-order.svg" alt="Order Flow" width="600">
</p>

> 1. **Katalog** → 2. **Keranjang** → 3. **Checkout** → 4. **QRIS Payment** → 5. **Auto Verify** → 6. **Notifikasi Berhasil**

---

### 📁 Struktur Proyek

```
telegram-auto-order-bot/
├── bot.py                          # 🤖 Bot utama (semua handler)
├── config.yaml                     # ⚙️ Konfigurasi aktif (gitignored)
├── config.example.yaml             # 📋 Template konfigurasi
├── .env.example                    # 🔑 Template environment variables
├── requirements.txt                # 📦 Dependencies Python
├── Dockerfile                      # 🐳 Docker build
├── docker-compose.yml              # 🐳 Docker Compose config
├── telegram-auto-order-bot.service # 🔵 systemd service file
├── LICENSE                         # 📝 MIT License
├── README.md                       # 📖 Dokumentasi ini
├── assets/                         # 🎨 Logo & diagram
│   ├── logo.svg
│   ├── architecture.svg
│   ├── flow-order.svg
│   └── flow-payment.svg
├── payments/
│   ├── __init__.py
│   └── klikqris.py                 # 💳 KlikQRIS API wrapper
├── database/
│   ├── __init__.py
│   └── models.py                   # 🗄️ SQLite database models
└── data/
    └── bot.db                      # 🗄️ Database SQLite (auto-generated)
```

---

### 🧪 Testing

```bash
# Gunakan mode sandbox
export KLIKQRIS_MODE=sandbox

# Jalankan bot
python bot.py
```

> Semua transaksi dalam mode sandbox **tidak menggunakan uang sungguhan**.

---

### 🛡️ Keamanan

| Aturan | Detail |
|---|---|
| 🔐 Jangan commit `.env` / `config.yaml` | Sudah di `.gitignore` |
| 🔑 Gunakan env vars untuk credential | `${VAR}` substitution di config |
| 🔒 HTTPS untuk webhook | Wajib untuk Telegram Bot API |
| ✅ Verifikasi signature webhook | KlikQRIS webhook validation |
| 🏃 Non-root user di Docker | `USER bot` di Dockerfile |
| 🚫 Rate limiting | Bawaan python-telegram-bot |

---

### 🤝 Kontribusi

Kontribusi selalu diterima!

1. **Fork** repository ini
2. **Buat branch** fitur: `git checkout -b fitur/keren`
3. **Commit** perubahan: `git commit -m 'Tambah fitur keren'`
4. **Push** ke branch: `git push origin fitur/keren`
5. Buka **Pull Request**

---

### 📝 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

### 📞 Bantuan

| Cara | Link |
|---|---|
| Buka Issue di GitHub | [Issues](https://github.com/mocasus/telegram-auto-order-bot/issues) |
| Perintah `/bantuan` di bot | Dalam Telegram |

---

<p align="center">
  <strong>Dibangun dengan ❤️ menggunakan Python dan python-telegram-bot</strong>
</p>

</details>

<details>
<summary><strong>🇬🇧 English</strong></summary>

<br>

> Complete Telegram bot for product catalog, shopping cart, checkout, and QRIS payments — all inside Telegram.

---

### 🚀 Quick Start — 3 Steps

**1. Clone the repo**
```bash
git clone https://github.com/mocasus/telegram-auto-order-bot.git
cd telegram-auto-order-bot
```

**2. Set up config**
```bash
cp .env.example .env
nano .env   # fill in bot token & API key
```

**3. Run**
```bash
pip install -r requirements.txt
python bot.py
```

✅ Bot runs immediately with **SQLite** (zero-config).

#### Minimum Requirements

| Requirement | Detail |
|---|---|
| Python 3.11+ | [python.org](https://python.org) |
| Telegram Bot Token | from [@BotFather](https://t.me/BotFather) |
| KlikQRIS Account | API Key + Merchant ID |

---

### ✨ Features

| Feature | Description |
|---|---|
| 🛍️ **Product Catalog** | Browse products by category with inline keyboard navigation |
| 🛒 **Shopping Cart** | Add, remove, adjust quantity, and clear cart |
| 💳 **QRIS Checkout** | Generate QRIS code for payment + auto verification |
| 📦 **Order History** | View all orders and their status |
| ⚙️ **Admin Panel** | Admin dashboard: manage products, orders, store summary |
| 🔔 **Auto Notifications** | 10-second polling + webhook callback for payment status |
| ⏱️ **30-Minute Timeout** | Orders auto-cancelled if unpaid |
| 🔐 **Sandbox Mode** | Test without real money |

---

### 🗄️ Database Options

| Feature | SQLite | PostgreSQL |
|---|---|---|
| Configuration | Zero-config, works out of the box | Requires install & setup |
| Scalability | Single-server, lightweight | Multi-connection, production-ready |
| Best for | Development, small-medium bots | Production, high-traffic |
| Setup | `database.path: "data/bot.db"` | `DATABASE_URL=postgresql://...` |

---

### 🖥️ Deploy Options

#### Comparison

| Method | Difficulty | Cost | Auto-restart | Best for |
|---|---|---|---|---|
| **PM2** | ⭐ Easy | Free | ✅ | Small VPS |
| **systemd** | ⭐⭐ Medium | Free | ✅ | VPS/Linux server |
| **Docker** | ⭐⭐ Medium | Free | ✅ | Any platform |
| **Railway** | ⭐ Easy | ~$5/mo | ✅ | Zero-ops deploy |
| **Render** | ⭐ Easy | Free tier | ✅ | Zero-ops deploy |

---

#### 🟢 PM2 (Easiest)

```bash
# 1. Install PM2
npm install -g pm2

# 2. Run bot
pm2 start bot.py --name "telegram-bot" --interpreter python3

# 3. Auto-start on reboot
pm2 save
pm2 startup

# Monitoring
pm2 status
pm2 logs telegram-bot
```

> PM2 is a Node.js process manager that can also run Python. Simplest option for small VPS.

---

#### 🔵 systemd (Linux Server)

```bash
# 1. Set up app directory
sudo mkdir -p /opt/telegram-auto-order-bot
sudo cp -r . /opt/telegram-auto-order-bot/
cd /opt/telegram-auto-order-bot

# 2. Create virtualenv & install
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env && nano .env

# 4. Install & run service
sudo cp telegram-auto-order-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now telegram-auto-order-bot

# Monitoring
sudo systemctl status telegram-auto-order-bot
sudo journalctl -u telegram-auto-order-bot -f
```

> Best option for Linux VPS. Fully integrated with OS, auto-restart, and journald logging.

---

#### 🐳 Docker

```bash
# Docker Compose (recommended)
cp .env.example .env && nano .env
docker compose up -d

# Monitoring
docker compose logs -f bot
```

<details>
<summary>Docker Run (manual)</summary>

```bash
docker build -t telegram-auto-order-bot .
docker run -d \
  --name telegram-auto-order-bot \
  --env-file .env \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  telegram-auto-order-bot
```
</details>

---

#### 🚂 Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new)

> Instant deploy to Railway. PaaS with auto-deploy from GitHub, logging, and environment variables UI.

```bash
# 1. Fork/clone this repo to your GitHub
# 2. Click the "Deploy on Railway" button above
# 3. Fill in environment variables in Railway dashboard
# 4. Done! Bot is running
```

**railway.json** (optional, for deploy config):
```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "python bot.py",
    "healthcheckPath": "/",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

---

#### ⚡ Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

> Free deploy to Render with free tier. Supports background workers for Telegram bots.

**render.yaml**:
```yaml
services:
  - type: worker
    name: telegram-auto-order-bot
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: python bot.py
    envVars:
      - key: TELEGRAM_BOT_TOKEN
        sync: false
      - key: KLIKQRIS_API_KEY
        sync: false
      - key: KLIKQRIS_MERCHANT_ID
        sync: false
      - key: KLIKQRIS_MODE
        value: sandbox
      - key: ADMIN_USER_ID
        sync: false
```

---

### 🔧 Full Configuration

#### `.env` — Environment Variables

| Variable | Description | Default |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | *(required)* |
| `KLIKQRIS_API_KEY` | KlikQRIS API Key | *(required)* |
| `KLIKQRIS_MERCHANT_ID` | Merchant ID | *(required)* |
| `KLIKQRIS_MODE` | `sandbox` or `production` | `sandbox` |
| `ADMIN_USER_ID` | Admin Telegram User ID | *(required)* |
| `DATABASE_URL` | PostgreSQL URL (optional) | *(SQLite default)* |
| `WEBHOOK_URL` | Webhook callback URL | *(empty)* |
| `CONFIG_PATH` | Path to config.yaml | `config.yaml` |

#### `config.yaml` — All Options

```yaml
bot:
  token: "BOT_TOKEN"          # Token from @BotFather
  name: "BotName"             # Display name
  username: "BotUsername"     # Bot username (without @)

klikqris:
  api_key: "API_KEY"          # KlikQRIS API Key
  merchant_id: "MERCHANT_ID"  # Merchant ID
  mode: sandbox               # sandbox | production
  timeout: 30                 # Request timeout (seconds)
  polling_interval: 10        # Status check interval (seconds)
  max_polling_attempts: 30    # Max polling before expiry

database:
  path: "data/bot.db"         # SQLite file path (ignore if using PostgreSQL)
  url: ""                     # PostgreSQL URL (optional): postgresql://user:pass@host/db

webhook:
  enabled: false              # true = webhook, false = polling
  url: "https://..."          # Webhook URL (HTTPS required)
  port: 8443                  # Webhook server port

admin:
  user_id: 123456789          # Primary admin user ID
  additional_ids: []          # Additional admins

store:
  name: "Online Store"        # Store name
  currency: "IDR"             # Currency
  currency_symbol: "Rp"       # Symbol
  admin_fee: 0                # Admin fee per transaction
  tax_percent: 0              # Tax (percentage)
```

---

### 🔌 KlikQRIS API

#### Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/v1/qris/create` | Create new QRIS payment |
| `GET` | `/v1/qris/status/{order_id}` | Check payment status |
| `GET` | `/v1/qris/history?page=N` | Transaction history |
| `POST` | Webhook Callback | Payment notification |

> **Sandbox Mode:** Use `KLIKQRIS_MODE=sandbox` for testing without real money.

---

### 🎮 Usage

#### Bot Commands

| Command | Function |
|---|---|
| `/start` | Main menu with inline buttons |
| `/help` | Help center |
| `/menu` | Back to main menu |
| `/cancel` | Cancel current operation |

#### Shopping Flow

<p align="center">
  <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/flow-order.svg" alt="Order Flow" width="600">
</p>

> 1. **Catalog** → 2. **Cart** → 3. **Checkout** → 4. **QRIS Payment** → 5. **Auto Verify** → 6. **Success Notification**

---

### 📁 Project Structure

```
telegram-auto-order-bot/
├── bot.py                          # 🤖 Main bot (all handlers)
├── config.yaml                     # ⚙️ Active config (gitignored)
├── config.example.yaml             # 📋 Config template
├── .env.example                    # 🔑 Environment variables template
├── requirements.txt                # 📦 Python dependencies
├── Dockerfile                      # 🐳 Docker build
├── docker-compose.yml              # 🐳 Docker Compose config
├── telegram-auto-order-bot.service # 🔵 systemd service file
├── LICENSE                         # 📝 MIT License
├── README.md                       # 📖 This documentation
├── assets/                         # 🎨 Logo & diagrams
│   ├── logo.svg
│   ├── architecture.svg
│   ├── flow-order.svg
│   └── flow-payment.svg
├── payments/
│   ├── __init__.py
│   └── klikqris.py                 # 💳 KlikQRIS API wrapper
├── database/
│   ├── __init__.py
│   └── models.py                   # 🗄️ SQLite database models
└── data/
    └── bot.db                      # 🗄️ SQLite database (auto-generated)
```

---

### 🧪 Testing

```bash
# Use sandbox mode
export KLIKQRIS_MODE=sandbox

# Run bot
python bot.py
```

> All sandbox mode transactions use **no real money**.

---

### 🛡️ Security

| Rule | Detail |
|---|---|
| 🔐 Don't commit `.env` / `config.yaml` | Already in `.gitignore` |
| 🔑 Use env vars for credentials | `${VAR}` substitution in config |
| 🔒 HTTPS for webhook | Required by Telegram Bot API |
| ✅ Verify webhook signature | KlikQRIS webhook validation |
| 🏃 Non-root user in Docker | `USER bot` in Dockerfile |
| 🚫 Rate limiting | Built-in python-telegram-bot |

---

### 🤝 Contributing

Contributions are always welcome!

1. **Fork** this repository
2. **Create a branch**: `git checkout -b feature/cool-feature`
3. **Commit** changes: `git commit -m 'Add cool feature'`
4. **Push** to branch: `git push origin feature/cool-feature`
5. Open a **Pull Request**

---

### 📝 License

This project is licensed under the [MIT License](LICENSE).

---

### 📞 Support

| Method | Link |
|---|---|
| Open GitHub Issue | [Issues](https://github.com/mocasus/telegram-auto-order-bot/issues) |
| `/help` command in bot | Inside Telegram |

---

<p align="center">
  <strong>Built with ❤️ using Python and python-telegram-bot</strong>
</p>

</details>

---

<p align="center">
  <a href="https://github.com/mocasus/telegram-auto-order-bot">
    <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/logo.svg" alt="Logo" width="64">
  </a>
</p>
