# 🤖 Telegram Auto Order Bot

Bot Telegram dengan integrasi pembayaran **KlikQRIS** yang memungkinkan pelanggan untuk melihat katalog produk, menambahkan ke keranjang, checkout, dan membayar menggunakan QRIS — semuanya dari dalam Telegram.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![PTB](https://img.shields.io/badge/python--telegram--bot-v22%2B-blue)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

---

## ✨ Fitur

### 🛍️ Untuk Pelanggan
- **Katalog Produk** — Jelajahi produk berdasarkan kategori
- **Navigasi Inline Keyboard** — Semua menu menggunakan tombol inline Telegram
- **Keranjang Belanja** — Tambah, hapus, atur jumlah, dan kosongkan keranjang
- **Checkout QRIS** — Generate kode QRIS untuk pembayaran
- **Verifikasi Otomatis** — Polling status pembayaran setiap 10 detik
- **Notifikasi** — Dapatkan pemberitahuan saat pembayaran berhasil
- **Riwayat Pesanan** — Lihat semua pesanan dan statusnya
- **Pesan Bahasa Indonesia** — Semua pesan dalam Bahasa Indonesia

### ⚙️ Untuk Admin
- **Panel Admin** — Dashboard khusus admin dengan inline menu
- **Manajemen Produk** — Tambah produk baru via conversation flow
- **Lihat Semua Pesanan** — Monitor semua pesanan dengan filter status
- **Ringkasan Toko** — Lihat total pesanan, pendapatan, dan produk aktif

### 💳 Pembayaran
- **KlikQRIS API** — Integrasi penuh dengan API KlikQRIS
- **Mode Sandbox** — Uji coba tanpa uang sungguhan
- **Polling + Callback** — Dua mekanisme verifikasi pembayaran
- **Batas Waktu 30 Menit** — Pesanan otomatis dibatalkan jika tidak dibayar

---

## 🚀 Instalasi Cepat

### Prasyarat
- Python 3.11+
- Token Bot Telegram (dari [@BotFather](https://t.me/BotFather))
- Akun KlikQRIS (API Key & Merchant ID)

### 1. Clone Repository

```bash
git clone https://github.com/username/telegram-auto-order-bot.git
cd telegram-auto-order-bot
```

### 2. Setup Environment

```bash
# Buat virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
```

### 3. Konfigurasi

```bash
# Salin file environment
cp .env.example .env

# Edit .env dengan data Anda
nano .env
```

**Isi minimal:**
```env
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234gh...
KLIKQRIS_API_KEY=your_api_key_here
KLIKQRIS_MERCHANT_ID=your_merchant_id
KLIKQRIS_MODE=sandbox
ADMIN_USER_ID=123456789
```

Atau edit langsung `config.yaml`:
```bash
cp config.example.yaml config.yaml
nano config.yaml
```

### 4. Jalankan Bot

```bash
# Development / testing
python bot.py

# Production dengan polling
python bot.py
```

---

## 🐳 Docker

### Menggunakan Docker Compose

```bash
# Buat file .env dari template
cp .env.example .env
# Edit .env
nano .env

# Buat config.yaml dari template (jika belum ada)
cp config.example.yaml config.yaml

# Build dan jalankan
docker-compose up -d

# Lihat log
docker-compose logs -f bot
```

### Menggunakan Docker langsung

```bash
docker build -t telegram-auto-order-bot .
docker run -d \
  --name telegram-auto-order-bot \
  --env-file .env \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/data:/app/data \
  telegram-auto-order-bot
```

---

## 🖥️ Deployment Production

### systemd Service (Linux)

```bash
# 1. Setup direktori
sudo mkdir -p /opt/telegram-auto-order-bot
sudo cp -r . /opt/telegram-auto-order-bot/
sudo chown -R bot:bot /opt/telegram-auto-order-bot/

# 2. Setup virtualenv
cd /opt/telegram-auto-order-bot
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Konfigurasi
cp .env.example .env
nano .env

# 4. Install systemd service
sudo cp telegram-auto-order-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-auto-order-bot
sudo systemctl start telegram-auto-order-bot

# 5. Cek status
sudo systemctl status telegram-auto-order-bot
sudo journalctl -u telegram-auto-order-bot -f
```

---

## 📁 Struktur Proyek

```
telegram-auto-order-bot/
├── bot.py                          # Bot utama (semua handler)
├── config.yaml                     # Konfigurasi aktif (jangan di-commit)
├── config.example.yaml             # Template konfigurasi
├── .env.example                    # Template environment variables
├── .gitignore                      # File yang diabaikan Git
├── requirements.txt                # Dependencies Python
├── Dockerfile                      # Build Docker
├── docker-compose.yml              # Docker Compose config
├── telegram-auto-order-bot.service # systemd service file
├── LICENSE                         # MIT License
├── README.md                       # Dokumentasi ini
├── payments/
│   ├── __init__.py
│   └── klikqris.py                 # KlikQRIS API wrapper
├── database/
│   ├── __init__.py
│   └── models.py                   # SQLite database models
└── data/
    └── bot.db                      # Database SQLite (auto-generated)
```

---

## 🔧 Konfigurasi Lengkap

### `config.yaml` — Semua Opsi

```yaml
bot:
  token: "TOKEN_BOT"          # Token dari @BotFather
  name: "NamaBot"             # Nama tampilan
  username: "UsernameBot"     # Username bot

klikqris:
  api_key: "API_KEY"          # API Key KlikQRIS
  merchant_id: "MERCHANT_ID"  # Merchant ID
  mode: sandbox               # sandbox | production
  timeout: 30                 # Request timeout (detik)
  polling_interval: 10        # Interval cek status (detik)
  max_polling_attempts: 30    # Maksimal percobaan polling

database:
  path: "data/bot.db"         # Path file SQLite

webhook:
  enabled: false              # true = webhook, false = polling
  url: "https://..."          # URL webhook (HTTPS)
  port: 8443                  # Port webhook server

admin:
  user_id: 123456789          # User ID admin utama
  additional_ids: []          # Admin tambahan

toko:
  name: "Toko Online"         # Nama toko
  currency: "IDR"             # Mata uang
  currency_symbol: "Rp"       # Simbol mata uang
  admin_fee: 0                # Biaya admin per transaksi
  tax_percent: 0              # PPN (persentase)

pesan:
  start: "..."                # Pesan /start
  bantuan: "..."              # Pesan /bantuan

kategori:                     # Daftar kategori produk
  - id: "makanan"
    nama: "🍔 Makanan"
    deskripsi: "Aneka makanan"

produk:                       # Daftar produk
  - id: "produk-1"
    nama: "Nama Produk"
    harga: 25000
    deskripsi: "Deskripsi..."
    kategori: "makanan"
    stok: 100
    emoji: "🍛"
```

---

## 🔌 KlikQRIS API

### Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/v1/qris/create` | Buat pembayaran QRIS baru |
| GET | `/v1/qris/status/{order_id}` | Cek status pembayaran |
| GET | `/v1/qris/history?page=N` | Riwayat transaksi |
| POST | Webhook Callback | Notifikasi pembayaran |

### Mode Sandbox

Untuk testing, gunakan `mode: sandbox` di config. API endpoint tetap sama tapi gunakan API key sandbox dari KlikQRIS.

---

## 🎮 Penggunaan

### Perintah Bot (Commands)

| Command | Deskripsi |
|---------|-----------|
| `/start` | Menu utama dengan tombol inline |
| `/bantuan` | Pusat bantuan |
| `/menu` | Kembali ke menu utama |
| `/cancel` | Batalkan operasi yang sedang berjalan |

### Alur Belanja

1. **Katalog** → Pilih kategori → Pilih produk → Tambah ke keranjang
2. **Keranjang** → Review item → Checkout
3. **Checkout** → Konfirmasi pesanan → Generate QRIS
4. **Pembayaran** → Scan QRIS → Bot cek otomatis → Notifikasi berhasil

### Panel Admin

1. Klik **⚙️ Panel Admin** di menu utama
2. **📋 Semua Pesanan** — Lihat semua pesanan
3. **📦 Kelola Produk** — Lihat daftar produk
4. **➕ Tambah Produk** — Tambah produk baru via wizard
5. **📊 Ringkasan** — Statistik toko

---

## 🧪 Testing

### Mode Sandbox
```bash
# Set mode ke sandbox
export KLIKQRIS_MODE=sandbox

# Jalankan bot
python bot.py
```

Semua transaksi dalam mode sandbox **tidak menggunakan uang sungguhan**.

---

## 🛡️ Keamanan

- 🔐 **Jangan commit `.env` atau `config.yaml`** ke repository
- 🔑 Gunakan environment variables untuk credential sensitif
- 🔒 Webhook menggunakan HTTPS
- ✅ Verifikasi signature webhook KlikQRIS
- 🚫 Rate limiting bawaan python-telegram-bot
- 🏃 Bot berjalan sebagai user non-root di Docker

---

## 🤝 Kontribusi

Kontribusi selalu diterima! Silakan:

1. Fork repository
2. Buat branch fitur (`git checkout -b fitur/keren`)
3. Commit perubahan (`git commit -m 'Tambah fitur keren'`)
4. Push ke branch (`git push origin fitur/keren`)
5. Buat Pull Request

---

## 📝 Lisensi

Proyek ini dilisensikan di bawah [MIT License](LICENSE).

---

## 📞 Bantuan

Jika mengalami masalah atau memiliki pertanyaan:

- Buka [Issue](https://github.com/username/telegram-auto-order-bot/issues) di GitHub
- Hubungi admin melalui bot dengan perintah `/bantuan`

---

**Dibuat dengan ❤️ menggunakan Python dan python-telegram-bot**
