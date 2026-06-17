# 🤖 Telegram Auto Order Bot

<p align="center">
  <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/logo.svg" alt="Logo" width="200">
</p>

<p align="center">
  <strong>🇮🇩 Bot Telegram dengan integrasi pembayaran KlikQRIS</strong><br>
  <em>🇬🇧 Telegram Bot with KlikQRIS payment integration</em>
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

> **🇮🇩** Bot Telegram lengkap untuk katalog produk, keranjang belanja, checkout, dan pembayaran QRIS — semuanya dari dalam Telegram.
>
> **🇬🇧** Complete Telegram bot for product catalog, shopping cart, checkout, and QRIS payments — all inside Telegram.

---

## 🚀 Quick Start · Mulai Cepat

<table>
<tr>
<td width="50%">

### 🇮🇩 3 Langkah

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

</td>
<td width="50%">

### 🇬🇧 3 Steps

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

</td>
</tr>
</table>

### Prasyarat Minimal · Minimum Requirements

| 🇮🇩 Kebutuhan | 🇬🇧 Requirement | Detail |
|---|---|---|
| Python 3.11+ | Python 3.11+ | [python.org](https://python.org) |
| Token Bot Telegram | Telegram Bot Token | dari [@BotFather](https://t.me/BotFather) |
| Akun KlikQRIS | KlikQRIS Account | API Key + Merchant ID |

---

## ✨ Fitur · Features

<table>
<tr>
<th width="5%"></th>
<th width="47%">🇮🇩 Bahasa Indonesia</th>
<th width="48%">🇬🇧 English</th>
</tr>
<tr>
<td>🛍️</td>
<td><strong>Katalog Produk</strong> — Jelajahi produk berdasarkan kategori dengan navigasi inline keyboard</td>
<td><strong>Product Catalog</strong> — Browse products by category with inline keyboard navigation</td>
</tr>
<tr>
<td>🛒</td>
<td><strong>Keranjang Belanja</strong> — Tambah, hapus, atur jumlah, dan kosongkan keranjang</td>
<td><strong>Shopping Cart</strong> — Add, remove, adjust quantity, and clear cart</td>
</tr>
<tr>
<td>💳</td>
<td><strong>Checkout QRIS</strong> — Generate kode QRIS untuk pembayaran + verifikasi otomatis</td>
<td><strong>QRIS Checkout</strong> — Generate QRIS code for payment + auto verification</td>
</tr>
<tr>
<td>📦</td>
<td><strong>Riwayat Pesanan</strong> — Lihat semua pesanan dan statusnya</td>
<td><strong>Order History</strong> — View all orders and their status</td>
</tr>
<tr>
<td>⚙️</td>
<td><strong>Panel Admin</strong> — Dashboard admin: kelola produk, pesanan, ringkasan toko</td>
<td><strong>Admin Panel</strong> — Admin dashboard: manage products, orders, store summary</td>
</tr>
<tr>
<td>🔔</td>
<td><strong>Notifikasi Otomatis</strong> — Polling 10-detik + webhook callback untuk status pembayaran</td>
<td><strong>Auto Notifications</strong> — 10-second polling + webhook callback for payment status</td>
</tr>
<tr>
<td>⏱️</td>
<td><strong>Batas Waktu 30 Menit</strong> — Pesanan otomatis dibatalkan jika tidak dibayar</td>
<td><strong>30-Minute Timeout</strong> — Orders auto-cancelled if unpaid</td>
</tr>
<tr>
<td>🔐</td>
<td><strong>Mode Sandbox</strong> — Uji coba tanpa uang sungguhan</td>
<td><strong>Sandbox Mode</strong> — Test without real money</td>
</tr>
</table>

---

## 🗄️ Database · Pilihan Database

| Fitur | SQLite | PostgreSQL |
|---|---|---|
| **🇮🇩 Konfigurasi** | Zero-config, langsung pakai | Perlu install & setup |
| **🇬🇧 Configuration** | Zero-config, works out of the box | Requires install & setup |
| **🇮🇩 Skalabilitas** | Single-server, ringan | Multi-connection, production-ready |
| **🇬🇧 Scalability** | Single-server, lightweight | Multi-connection, production-ready |
| **🇮🇩 Cocok untuk** | Development, bot kecil-menengah | Production, high-traffic |
| **🇬🇧 Best for** | Development, small-medium bots | Production, high-traffic |
| **🇮🇩 Setup** | `database.path: "data/bot.db"` | `DATABASE_URL=postgresql://...` |
| **🇬🇧 Setup** | `database.path: "data/bot.db"` | `DATABASE_URL=postgresql://...` |

> **🇮🇩 Rekomendasi:** Gunakan **SQLite** untuk memulai. Upgrade ke **PostgreSQL** saat bot Anda melayani ratusan user concurrent.
>
> **🇬🇧 Recommendation:** Start with **SQLite**. Upgrade to **PostgreSQL** when your bot serves hundreds of concurrent users.

---

## 🖥️ Deployment · Opsi Deploy

### Perbandingan · Comparison

| Metode | 🇮🇩 Tingkat Kesulitan | 🇬🇧 Difficulty | 🇮🇩 Biaya | 🇬🇧 Cost | Auto-restart | Cocok untuk |
|---|---|---|---|---|---|---|
| **PM2** | ⭐ Mudah/Easy | ⭐ Easy | Gratis/Free | ✅ | VPS kecil |
| **systemd** | ⭐⭐ Menengah | ⭐⭐ Medium | Gratis/Free | ✅ | VPS/Linux server |
| **Docker** | ⭐⭐ Menengah | ⭐⭐ Medium | Gratis/Free | ✅ | Any platform |
| **Railway** | ⭐ Mudah/Easy | ⭐ Easy | Mulai ~$5/bln | ~$5/mo | ✅ | Zero-ops deploy |
| **Render** | ⭐ Mudah/Easy | ⭐ Easy | Mulai gratis | Free tier | ✅ | Zero-ops deploy |

---

### 🟢 PM2 (Termudah · Easiest)

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

> 🇮🇩 PM2 adalah process manager Node.js yang juga bisa menjalankan Python. Paling sederhana untuk VPS kecil.
> 🇬🇧 PM2 is a Node.js process manager that can also run Python. Simplest option for small VPS.

---

### 🔵 systemd (Linux Server)

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

> 🇮🇩 Opsi terbaik untuk VPS Linux. Terintegrasi penuh dengan sistem operasi, auto-restart, dan logging ke journald.
> 🇬🇧 Best option for Linux VPS. Fully integrated with OS, auto-restart, and journald logging.

---

### 🐳 Docker

```bash
# Docker Compose (recommended)
cp .env.example .env && nano .env
docker compose up -d

# Monitoring
docker compose logs -f bot
```

<details>
<summary>🇮🇩 Docker Run (manual) · 🇬🇧 Docker Run (manual)</summary>

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

### 🚂 Railway

[![Deploy on Railway](https://railway.com/button.svg)](https://railway.com/new)

> 🇮🇩 Deploy instan ke Railway. Platform-as-a-Service dengan auto-deploy dari GitHub, logging, dan environment variables UI.
> 🇬🇧 Instant deploy to Railway. PaaS with auto-deploy from GitHub, logging, and environment variables UI.

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

### ⚡ Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com)

> 🇮🇩 Deploy gratis ke Render dengan free tier. Mendukung background worker untuk bot Telegram.
> 🇬🇧 Free deploy to Render with free tier. Supports background workers for Telegram bots.

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

## 🔧 Konfigurasi Lengkap · Full Configuration

<details>
<summary>🇮🇩 Klik untuk lihat semua opsi · 🇬🇧 Click to see all options</summary>

### `.env` — Environment Variables

| Variable | 🇮🇩 Deskripsi | 🇬🇧 Description | Default |
|---|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token bot dari @BotFather | Bot token from @BotFather | *(wajib/required)* |
| `KLIKQRIS_API_KEY` | API Key KlikQRIS | KlikQRIS API Key | *(wajib/required)* |
| `KLIKQRIS_MERCHANT_ID` | Merchant ID | Merchant ID | *(wajib/required)* |
| `KLIKQRIS_MODE` | `sandbox` atau `production` | `sandbox` or `production` | `sandbox` |
| `ADMIN_USER_ID` | User ID admin Telegram | Admin Telegram User ID | *(wajib/required)* |
| `DATABASE_URL` | URL PostgreSQL (opsional) | PostgreSQL URL (optional) | *(SQLite default)* |
| `WEBHOOK_URL` | URL webhook callback | Webhook callback URL | *(kosong/empty)* |
| `CONFIG_PATH` | Path ke config.yaml | Path to config.yaml | `config.yaml` |

### `config.yaml` — Semua Opsi · All Options

```yaml
bot:
  token: "TOKEN_BOT"          # Token dari @BotFather
  name: "NamaBot"             # Nama tampilan · Display name
  username: "UsernameBot"     # Username bot (tanpa @)

klikqris:
  api_key: "API_KEY"          # API Key KlikQRIS
  merchant_id: "MERCHANT_ID"  # Merchant ID
  mode: sandbox               # sandbox | production
  timeout: 30                 # Request timeout (detik/seconds)
  polling_interval: 10        # Interval cek status (detik/seconds)
  max_polling_attempts: 30    # Maks polling sebelum expired

database:
  path: "data/bot.db"         # Path file SQLite (abaikan jika pakai PostgreSQL)
  url: ""                     # PostgreSQL URL (opsional): postgresql://user:pass@host/db

webhook:
  enabled: false              # true = webhook, false = polling
  url: "https://..."          # URL webhook (HTTPS required)
  port: 8443                  # Port webhook server

admin:
  user_id: 123456789          # User ID admin utama · Primary admin
  additional_ids: []          # Admin tambahan · Additional admins

toko:
  name: "Toko Online"         # Nama toko · Store name
  currency: "IDR"             # Mata uang · Currency
  currency_symbol: "Rp"       # Simbol · Symbol
  admin_fee: 0                # Biaya admin per transaksi
  tax_percent: 0              # PPN (persentase/percentage)
```

</details>

---

## 🔌 KlikQRIS API

### Endpoints

| Method | Endpoint | 🇮🇩 Deskripsi | 🇬🇧 Description |
|---|---|---|---|
| `POST` | `/v1/qris/create` | Buat pembayaran QRIS baru | Create new QRIS payment |
| `GET` | `/v1/qris/status/{order_id}` | Cek status pembayaran | Check payment status |
| `GET` | `/v1/qris/history?page=N` | Riwayat transaksi | Transaction history |
| `POST` | Webhook Callback | Notifikasi pembayaran | Payment notification |

> 🇮🇩 **Mode Sandbox:** Gunakan `KLIKQRIS_MODE=sandbox` untuk testing tanpa uang sungguhan.
> 🇬🇧 **Sandbox Mode:** Use `KLIKQRIS_MODE=sandbox` for testing without real money.

---

## 🎮 Penggunaan · Usage

### Perintah Bot · Bot Commands

| Command | 🇮🇩 Fungsi | 🇬🇧 Function |
|---|---|---|
| `/start` | Menu utama dengan tombol inline | Main menu with inline buttons |
| `/bantuan` | Pusat bantuan | Help center |
| `/menu` | Kembali ke menu utama | Back to main menu |
| `/cancel` | Batalkan operasi yang sedang berjalan | Cancel current operation |

### Alur Belanja · Shopping Flow

<p align="center">
  <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/flow-order.svg" alt="Order Flow" width="600">
</p>

> 🇮🇩 1. **Katalog** → 2. **Keranjang** → 3. **Checkout** → 4. **QRIS Payment** → 5. **Auto Verify** → 6. **Notifikasi Berhasil**
>
> 🇬🇧 1. **Catalog** → 2. **Cart** → 3. **Checkout** → 4. **QRIS Payment** → 5. **Auto Verify** → 6. **Success Notification**

---

## 📁 Struktur Proyek · Project Structure

```
telegram-auto-order-bot/
├── bot.py                          # 🤖 Bot utama · Main bot (all handlers)
├── config.yaml                     # ⚙️ Konfigurasi aktif · Active config (gitignored)
├── config.example.yaml             # 📋 Template konfigurasi · Config template
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

## 🧪 Testing

```bash
# Gunakan mode sandbox · Use sandbox mode
export KLIKQRIS_MODE=sandbox

# Jalankan bot · Run bot
python bot.py
```

> 🇮🇩 Semua transaksi dalam mode sandbox **tidak menggunakan uang sungguhan**.
> 🇬🇧 All sandbox mode transactions use **no real money**.

---

## 🛡️ Keamanan · Security

| 🛡️ Aturan · Rule | Detail |
|---|---|
| 🔐 Jangan commit `.env` / `config.yaml` | Sudah di `.gitignore` |
| 🔑 Gunakan env vars untuk credential | `${VAR}` substitution di config |
| 🔒 HTTPS untuk webhook | Wajib untuk Telegram Bot API |
| ✅ Verifikasi signature webhook | KlikQRIS webhook validation |
| 🏃 Non-root user di Docker | `USER bot` di Dockerfile |
| 🚫 Rate limiting | Bawaan python-telegram-bot |

---

## 🤝 Kontribusi · Contributing

🇮🇩 Kontribusi selalu diterima!
🇬🇧 Contributions are always welcome!

1. **Fork** repository ini
2. **Buat branch** fitur: `git checkout -b fitur/keren`
3. **Commit** perubahan: `git commit -m 'Tambah fitur keren'`
4. **Push** ke branch: `git push origin fitur/keren`
5. Buka **Pull Request**

---

## 📝 Lisensi · License

Proyek ini dilisensikan di bawah [MIT License](LICENSE).
This project is licensed under the [MIT License](LICENSE).

---

## 📞 Bantuan · Support

| 🇮🇩 Cara | 🇬🇧 Method | Link |
|---|---|---|
| Buka Issue di GitHub | Open GitHub Issue | [Issues](https://github.com/mocasus/telegram-auto-order-bot/issues) |
| Perintah `/bantuan` di bot | `/bantuan` command in bot | Dalam Telegram |

---

<p align="center">
  <strong>🇮🇩 Dibangun dengan ❤️ menggunakan Python dan python-telegram-bot</strong><br>
  <strong>🇬🇧 Built with ❤️ using Python and python-telegram-bot</strong>
</p>

<p align="center">
  <a href="https://github.com/mocasus/telegram-auto-order-bot">
    <img src="https://raw.githubusercontent.com/mocasus/telegram-auto-order-bot/main/assets/logo.svg" alt="Logo" width="64">
  </a>
</p>
