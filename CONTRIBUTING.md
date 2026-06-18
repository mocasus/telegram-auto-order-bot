# 🤝 Panduan Kontribusi / Contributing Guide

Terima kasih telah tertarik untuk berkontribusi pada **Telegram Auto Order Bot**! 🎉

Thank you for your interest in contributing to **Telegram Auto Order Bot**! 🎉

---

## 🌐 Bahasa / Languages

- [🇮🇩 Bahasa Indonesia](#-bahasa-indonesia)
- [🇬🇧 English](#-english)

---

## 🇮🇩 Bahasa Indonesia

### 📋 Daftar Isi

- [Cara Berkontribusi](#cara-berkontribusi)
- [Melaporkan Bug](#melaporkan-bug)
- [Mengusulkan Fitur](#mengusulkan-fitur)
- [Pull Request](#pull-request)
- [Style Guide](#style-guide)
- [Struktur Commit](#struktur-commit)
- [Lingkungan Development](#lingkungan-development)

### Cara Berkontribusi

Ada beberapa cara untuk berkontribusi:

1. **Melaporkan bug** — buka [issue baru](../../issues/new/choose) dengan template bug report
2. **Mengusulkan fitur** — buka [issue baru](../../issues/new/choose) dengan template feature request
3. **Memperbaiki bug** — pilih issue dengan label `bug` dan buat PR
4. **Menambah fitur** — diskusikan dulu di issue sebelum coding
5. **Memperbaiki dokumentasi** — typo, penjelasan, atau contoh
6. **Menulis test** — meningkatkan coverage

### Melaporkan Bug

Gunakan template [Bug Report](../../issues/new?template=bug_report.md) dan sertakan:

- Deskripsi jelas tentang bug
- Langkah-langkah reproduksi
- Hasil yang diharapkan vs aktual
- Environment (OS, Python version, deployment method)
- Log error (jika ada)

### Mengusulkan Fitur

Gunakan template [Feature Request](../../issues/new?template=feature_request.md) dan jelaskan:

- Apa fitur yang Anda inginkan
- Mengapa fitur ini berguna
- Bagaimana fitur ini bisa bekerja
- Alternatif yang sudah dipertimbangkan

### Pull Request

#### Proses

1. **Fork** repository ini
2. **Clone** fork Anda: `git clone https://github.com/YOUR_USERNAME/telegram-auto-order-bot.git`
3. **Buat branch** untuk fitur/fix Anda: `git checkout -b feat/nama-fitur`
4. **Buat perubahan** dan commit dengan pesan yang jelas
5. **Push** ke fork Anda: `git push origin feat/nama-fitur`
6. Buka **Pull Request** ke `main` branch

#### Checklist PR

Pastikan PR Anda:

- ✅ Mengikuti style guide Python (PEP 8)
- ✅ Menambahkan docstring untuk fungsi baru
- ✅ Ditest secara lokal (minimal mode sandbox)
- ✅ Tidak menambahkan warning baru
- ✅ Memperbarui dokumentasi jika perlu
- ✅ Commit message jelas dan deskriptif

### Style Guide

#### Python

Ikuti [PEP 8](https://peps.python.org/pep-0008/):

- Indentasi 4 spasi (bukan tab)
- Maximum line length: 88 karakter (Black formatter)
- Gunakan type hints untuk fungsi
- Docstring untuk class dan fungsi public

**Contoh:**

```python
async def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Ambil produk berdasarkan ID.
    
    Args:
        product_id: ID produk yang dicari
        
    Returns:
        Dict berisi data produk, atau None jika tidak ditemukan
    """
    ...
```

#### YAML

- Indentasi 2 spasi
- Key menggunakan `snake_case`
- Tambahkan komentar untuk opsi yang tidak jelas

### Struktur Commit

Gunakan [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: Fitur baru
- `fix`: Bug fix
- `docs`: Dokumentasi
- `style`: Formatting (tidak mengubah logic)
- `refactor`: Refactoring (tidak mengubah fungsionalitas)
- `test`: Menambah/update test
- `chore`: Maintenance (dependency, build, dll)
- `perf`: Performance improvement

**Contoh:**

```bash
git commit -m "feat(payment): tambah dukungan webhook callback KlikQRIS"
git commit -m "fix(cart): perbaiki bug jumlah item tidak update"
git commit -m "docs(readme): perbarui instruksi deploy Docker"
```

### Lingkungan Development

#### Setup

```bash
# Clone repository
git clone https://github.com/mocasus/telegram-auto-order-bot.git
cd telegram-auto-order-bot

# Buat virtualenv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# atau: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup config
cp .env.example .env
cp config.example.yaml config.yaml
nano .env  # isi credentials Anda
```

#### Running

```bash
# Jalankan bot
python bot.py

# Atau dengan auto-reload (untuk development)
# Install watchdog: pip install watchdog
# watchmedo auto-restart -d . -p '*.py' -- python bot.py
```

#### Testing

Selalu test di **sandbox mode** sebelum production:

```bash
export KLIKQRIS_MODE=sandbox
python bot.py
```

Test checklist:

- [ ] `/start` dan menu utama muncul
- [ ] Katalog produk bisa dinavigasi
- [ ] Produk bisa ditambah ke keranjang
- [ ] Keranjang bisa dilihat dan diubah
- [ ] Checkout menghasilkan QRIS
- [ ] Admin panel bisa diakses
- [ ] Tidak ada error di log

---

## 🇬🇧 English

### 📋 Table of Contents

- [How to Contribute](#how-to-contribute)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Features](#suggesting-features)
- [Pull Requests](#pull-requests)
- [Style Guide](#style-guide-1)
- [Commit Structure](#commit-structure)
- [Development Environment](#development-environment)

### How to Contribute

You can contribute in several ways:

1. **Report bugs** — open a [new issue](../../issues/new/choose) with the bug report template
2. **Suggest features** — open a [new issue](../../issues/new/choose) with the feature request template
3. **Fix bugs** — pick an issue labeled `bug` and submit a PR
4. **Add features** — discuss in an issue first before coding
5. **Improve documentation** — typos, explanations, or examples
6. **Write tests** — increase test coverage

### Reporting Bugs

Use the [Bug Report](../../issues/new?template=bug_report.md) template and include:

- Clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Environment (OS, Python version, deployment method)
- Error logs (if any)

### Suggesting Features

Use the [Feature Request](../../issues/new?template=feature_request.md) template and explain:

- What feature you want
- Why this feature is useful
- How this feature could work
- Alternatives you've considered

### Pull Requests

#### Process

1. **Fork** this repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/telegram-auto-order-bot.git`
3. **Create a branch** for your feature/fix: `git checkout -b feat/feature-name`
4. **Make changes** and commit with clear messages
5. **Push** to your fork: `git push origin feat/feature-name`
6. Open a **Pull Request** to the `main` branch

#### PR Checklist

Make sure your PR:

- ✅ Follows Python style guide (PEP 8)
- ✅ Adds docstrings for new functions
- ✅ Is tested locally (at least sandbox mode)
- ✅ Doesn't introduce new warnings
- ✅ Updates documentation if needed
- ✅ Has clear and descriptive commit messages

### Style Guide

#### Python

Follow [PEP 8](https://peps.python.org/pep-0008/):

- 4-space indentation (no tabs)
- Maximum line length: 88 characters (Black formatter)
- Use type hints for functions
- Docstrings for public classes and functions

**Example:**

```python
async def get_product(product_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a product by ID.
    
    Args:
        product_id: Product ID to search for
        
    Returns:
        Dict containing product data, or None if not found
    """
    ...
```

#### YAML

- 2-space indentation
- Keys use `snake_case`
- Add comments for unclear options

### Commit Structure

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no logic change)
- `refactor`: Refactoring (no functionality change)
- `test`: Add/update tests
- `chore`: Maintenance (dependencies, build, etc)
- `perf`: Performance improvement

**Examples:**

```bash
git commit -m "feat(payment): add KlikQRIS webhook callback support"
git commit -m "fix(cart): fix item quantity not updating"
git commit -m "docs(readme): update Docker deployment instructions"
```

### Development Environment

#### Setup

```bash
# Clone repository
git clone https://github.com/mocasus/telegram-auto-order-bot.git
cd telegram-auto-order-bot

# Create virtualenv
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Setup config
cp .env.example .env
cp config.example.yaml config.yaml
nano .env  # fill in your credentials
```

#### Running

```bash
# Run the bot
python bot.py

# Or with auto-reload (for development)
# Install watchdog: pip install watchdog
# watchmedo auto-restart -d . -p '*.py' -- python bot.py
```

#### Testing

Always test in **sandbox mode** before production:

```bash
export KLIKQRIS_MODE=sandbox
python bot.py
```

Test checklist:

- [ ] `/start` and main menu appear
- [ ] Product catalog can be navigated
- [ ] Products can be added to cart
- [ ] Cart can be viewed and modified
- [ ] Checkout generates QRIS
- [ ] Admin panel is accessible
- [ ] No errors in logs

---

## 📜 Lisensi / License

Dengan berkontribusi, Anda menyetujui bahwa kontribusi Anda akan dilisensikan di bawah [MIT License](LICENSE) yang sama dengan proyek ini.

By contributing, you agree that your contributions will be licensed under the same [MIT License](LICENSE) as this project.

---

## 🙏 Terima Kasih / Thank You

Terima kasih telah meluangkan waktu untuk berkontribusi! 🎉

Thank you for taking the time to contribute! 🎉
