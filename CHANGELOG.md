# Changelog

All notable changes to **telegram-auto-order-bot** are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
versioning follows [SemVer](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] — 2026-06-30

First production-ready release. Battle-tested on live VPS deployment serving real customers via Telegram.

### Added
- 🛍️ **Product catalog** via inline keyboard (paginated, category-grouped)
- 🛒 **3-step order flow** — pick product → quantity → confirm
- 💳 **KlikQRIS integration** — auto QR generation, 30-second polling for payment verification
- 🏦 **Manual bank transfer** option with admin-approval flow
- ⏰ **Auto-cancel** for expired/unpaid orders (configurable timeout, default 15min)
- 📋 **Order history** per user via `/myorders`
- 🔧 **Admin commands**:
  - `/addproduct`, `/delproduct`, `/listproducts`
  - `/orders` — view all orders with status filter
  - `/setstatus <order_id> <status>` — update order state
  - `/broadcast` — message all customers
- 🗄️ **SQLite single-file DB** — no DB server setup needed
- 🚀 **Minimal deps** — only `python-telegram-bot` + `python-dotenv`
- 📦 **systemd unit** included for VPS deployment
- 🌐 **Bilingual README** — Bahasa Indonesia + English
- 🎨 **SVG assets** — logo, architecture diagram, order flow, payment flow

### Security
- Real `.env` excluded via `.gitignore`
- Admin actions whitelist-only (TG numeric IDs)
- Payment webhook signature validation (KlikQRIS)
- See [SECURITY.md](SECURITY.md) for full threat model

### Documentation
- README.md (11k+ chars, bilingual ID/EN)
- SPEC.md (full functional + non-functional spec)
- CONTRIBUTING.md (PR workflow, style guide)
- SECURITY.md (vulnerability disclosure)

---

## Template for future entries

```markdown
## [X.Y.Z] — YYYY-MM-DD

### Added
- New features

### Changed
- Modifications to existing behavior

### Deprecated
- Soon-to-be-removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Security patches
```
