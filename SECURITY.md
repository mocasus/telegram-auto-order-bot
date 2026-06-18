# 🛡️ Security Policy / Kebijakan Keamanan

## 🌐 Languages / Bahasa

- [🇬🇧 English](#english)
- [🇮🇩 Bahasa Indonesia](#bahasa-indonesia)

---

## 🇬🇧 English

### Supported Versions

We release security updates for the following versions:

| Version | Supported          |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

### Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **Email**: Send details to the repository owner (check GitHub profile)
2. **Private Security Advisory**: Use GitHub's [private vulnerability reporting](../../security/advisories/new)

Please include:

- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if you have one)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix & Disclosure**: Coordinated disclosure after fix is ready

### Security Best Practices

When using this bot:

#### 🔐 Credentials

- **Never commit** `.env` or `config.yaml` to git
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use different credentials for sandbox vs production

#### 🔒 Deployment

- Run bot as **non-root user** (Docker already does this)
- Use **HTTPS** for webhooks (required by Telegram)
- Keep dependencies up to date: `pip install --upgrade -r requirements.txt`
- Use firewall rules to restrict access to your server

#### 💾 Database

- Regularly backup your database
- Use strong passwords for PostgreSQL/MySQL
- Restrict database access to localhost (or trusted IPs)
- Don't expose database ports publicly

#### 🌐 Network

- Use webhook mode with HTTPS in production
- Validate webhook signatures (already implemented for KlikQRIS)
- Rate limit API requests if exposing webhook endpoint
- Use reverse proxy (nginx/caddy) for SSL termination

#### 📊 Monitoring

- Monitor logs for suspicious activity
- Set up alerts for failed authentication attempts
- Review admin access regularly
- Log all payment transactions

### Known Security Considerations

#### API Keys in Config Files

The bot uses a YAML config file that may contain sensitive data. Always:

- Keep `config.yaml` in `.gitignore` (already done)
- Use `${ENV_VAR}` substitution for secrets
- Set proper file permissions: `chmod 600 config.yaml`

#### Database Security

SQLite databases are stored locally without encryption by default:

- Use file system encryption if storing sensitive data
- Consider PostgreSQL with SSL for production
- Backup databases to encrypted storage

#### Admin Access

Admin users have full control over the bot:

- Only grant admin to trusted users
- Review `admin.user_id` and `admin.additional_ids` regularly
- Implement audit logs for admin actions (future feature)

---

## 🇮🇩 Bahasa Indonesia

### Versi yang Didukung

Kami merilis pembaruan keamanan untuk versi berikut:

| Versi   | Didukung           |
| ------- | ------------------ |
| main    | :white_check_mark: |
| < 1.0   | :x:                |

### Melaporkan Kerentanan

**Jangan laporkan kerentanan keamanan melalui GitHub issues publik.**

Sebagai gantinya, laporkan melalui salah satu metode berikut:

1. **Email**: Kirim detail ke pemilik repository (cek profil GitHub)
2. **Private Security Advisory**: Gunakan [private vulnerability reporting](../../security/advisories/new) GitHub

Mohon sertakan:

- Deskripsi kerentanan
- Langkah-langkah reproduksi
- Dampak potensial
- Saran perbaikan (jika ada)

### Yang Bisa Diharapkan

- **Konfirmasi**: Dalam 48 jam
- **Penilaian Awal**: Dalam 7 hari
- **Perbaikan & Pengungkapan**: Pengungkapan terkoordinasi setelah perbaikan siap

### Praktik Keamanan Terbaik

Saat menggunakan bot ini:

#### 🔐 Kredensial

- **Jangan commit** `.env` atau `config.yaml` ke git
- Gunakan environment variables untuk data sensitif
- Rotasi API keys secara berkala
- Gunakan kredensial berbeda untuk sandbox vs production

#### 🔒 Deployment

- Jalankan bot sebagai **non-root user** (Docker sudah melakukan ini)
- Gunakan **HTTPS** untuk webhook (wajib oleh Telegram)
- Perbarui dependencies: `pip install --upgrade -r requirements.txt`
- Gunakan firewall rules untuk membatasi akses ke server

#### 💾 Database

- Backup database secara berkala
- Gunakan password kuat untuk PostgreSQL/MySQL
- Batasi akses database ke localhost (atau IP terpercaya)
- Jangan expose port database secara publik

#### 🌐 Network

- Gunakan webhook mode dengan HTTPS di production
- Validasi webhook signatures (sudah diimplementasi untuk KlikQRIS)
- Rate limit API requests jika expose webhook endpoint
- Gunakan reverse proxy (nginx/caddy) untuk SSL termination

#### 📊 Monitoring

- Monitor log untuk aktivitas mencurigakan
- Setup alerts untuk failed authentication attempts
- Review admin access secara berkala
- Log semua transaksi pembayaran

### Pertimbangan Keamanan yang Diketahui

#### API Keys di File Config

Bot menggunakan file YAML config yang mungkin berisi data sensitif. Selalu:

- Simpan `config.yaml` di `.gitignore` (sudah dilakukan)
- Gunakan substitusi `${ENV_VAR}` untuk secrets
- Set permission file yang tepat: `chmod 600 config.yaml`

#### Keamanan Database

Database SQLite disimpan secara lokal tanpa enkripsi default:

- Gunakan file system encryption jika menyimpan data sensitif
- Pertimbangkan PostgreSQL dengan SSL untuk production
- Backup database ke storage terenkripsi

#### Akses Admin

Admin users memiliki kontrol penuh atas bot:

- Hanya berikan admin ke user terpercaya
- Review `admin.user_id` dan `admin.additional_ids` secara berkala
- Implementasi audit logs untuk admin actions (fitur masa depan)

---

## 🔒 Disclosure Policy

We follow **responsible disclosure**:

1. Reporter notifies us privately
2. We confirm and develop a fix
3. Fix is released
4. Public disclosure after users have time to update (typically 7-14 days)

Kami mengikuti **responsible disclosure**:

1. Pelapor memberi tahu kami secara privat
2. Kami konfirmasi dan develop fix
3. Fix dirilis
4. Pengungkapan publik setelah users punya waktu untuk update (biasanya 7-14 hari)

---

## 🙏 Thank You / Terima Kasih

Thank you for helping keep **Telegram Auto Order Bot** and its users safe!

Terima kasih telah membantu menjaga **Telegram Auto Order Bot** dan penggunanya tetap aman!
