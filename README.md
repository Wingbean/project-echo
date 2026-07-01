# Project Echo 📡

ระบบเว็บแอปพลิเคชันสำหรับค้นหาข้อมูลผู้ป่วยรายบุคคล (ตาม HN) จากฐานข้อมูล HosXP แบบ ad-hoc ไม่มี cache

## Features

- 🔍 **Per-HN Search** — ค้นหา eGFR, HbA1c, INR, Consult, OPD Flow, EMR ตามเลข HN แบบสด (query ตรงไป HosXP ทุกครั้ง)
- 🔐 **Google Login + Admin Approval** — ล็อกอินด้วย Gmail, ยืนยันอีเมล, และรอผู้ดูแลระบบอนุมัติก่อนใช้งานได้
- 🛠️ **Admin Panel** — อนุมัติ/ปิดใช้งาน/ลบผู้ใช้ และกำหนดสิทธิ์เข้าถึง Echo/EMR รายบุคคล
- 🔒 **Security** — CSRF protection, parameterized SQL, PHI (EMR) gated by per-user access flags
- 🌙 **Dark Mode** — รองรับธีมสว่าง/มืด
- 🇹🇭 **Thai Support** — รองรับภาษาไทยเต็มรูปแบบ (Noto Sans Thai)
- 📱 **Responsive** — ใช้งานได้ทุกอุปกรณ์

## Tech Stack

| Component       | Technology                                |
| --------------- | ------------------------------------------ |
| Backend         | Python + Flask                             |
| Template        | Jinja2                                     |
| Frontend        | HTML, CSS, JavaScript (no build step)      |
| Database        | HosXP (MySQL, read-only) + local SQLite (users, `instance/app.db`) |
| Auth            | Google OAuth (Authlib) + email verification |
| Package Manager | uv                                          |
| Container       | Docker + Gunicorn                          |

## Quick Start

### 1. Setup Environment

Create `.env` in the project root (no `.env.example` template — see [Environment Variables](#environment-variables) below for the full list) and fill in real values.

### 2. Run with Docker (Recommended)

```bash
docker compose up --build -d
# Access at http://localhost:5009
```

### 3. Run Locally with uv

```bash
# Install dependencies
uv sync

# Run development server
uv run python main.py
```

## Project Structure

```
project-echo/
├── app/                    # Flask application
│   ├── __init__.py         # App factory, CSRF, OAuth client, local DB table creation
│   ├── config.py           # Configuration from .env
│   ├── api/                # API routes + page views (routes_auth, routes_admin, routes_search, routes_barcode, views)
│   ├── models/              # HosXP connection + local users DB/model
│   ├── services/            # Business logic (HosXP query execution)
│   └── utils/               # Helpers, auth decorators, email sending
├── templates/               # Jinja2 templates
│   ├── base.html            # Base layout
│   ├── components/          # Reusable components
│   └── pages/                # Page templates
├── static/                  # CSS, JS, assets
│   ├── css/                 # Theme + main + components
│   └── js/                  # API client + utilities
├── sql/                     # SQL scripts (one .sql file per lookup type)
├── tests/                   # Test suite
├── Dockerfile               # Container config
├── docker-compose.yml       # Docker Compose
├── gunicorn.conf.py         # Gunicorn settings
└── pyproject.toml           # uv dependencies
```

## Data Flow

```
Browser → /api/<lookup> (requires login) → sql/<name>.sql → HosXP MySQL (pandas, no cache) → JSON response
```

There is no sync job, scheduler, or local cache of HosXP data — every search hits HosXP live. The only local database is the small SQLite `instance/app.db`, which stores user accounts (not patient data).

## Routes

### Pages (`views_bp`, `/`)

| Path | Description | Access |
| --- | --- | --- |
| `/login` | Google login button | public |
| `/pending-approval` | Shown while awaiting email verification / admin approval | logged in |
| `/` | Homepage — links to search tools | login required |
| `/consult`, `/flow_opd`, `/egfr`, `/a1c`, `/inr` | Per-HN lab/record search pages | login required |
| `/echo` | Integrated dashboard (labs + EMR) | login + `can_access_echo` |
| `/emr` | EMR search page | login + `can_access_emr` |
| `/admin` | Admin panel | `ADMIN_EMAILS` whitelist |

### API (`api_bp`, `/api`)

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| POST | `/api/egfr`, `/api/a1c`, `/api/inr`, `/api/consult`, `/api/flow_opd` | Per-HN lookups | login required |
| POST | `/api/emr` | EMR lookup, groups prescriptions by visit (`VN`) | `can_access_echo` OR `can_access_emr` |
| GET | `/auth/login`, `/auth/callback`, `/auth/logout` | Google OAuth login flow | public |
| GET | `/auth/verify-email/<token>` | Email verification link | public (signed token) |
| GET | `/api/admin/users` | List all users | admin |
| POST | `/api/admin/users/<id>/activate`, `/deactivate`, `/delete`, `/access` | Manage a user | admin |
| GET | `/api/test-db` | HosXP connection diagnostic | public |
| POST | `/api/barcode-trigger`, GET `/api/last-scanned` | Barcode scanner integration | public (CSRF-exempt) |

## Auth Model

Every page and API endpoint above (except the barcode/diagnostic endpoints) requires a logged-in, verified, admin-activated user:

1. User clicks "Login with Gmail" → Google OAuth (Authlib) → a `User` row is created/matched by Google's `sub` claim.
2. On first login, a signed, 24h-expiring verification link is emailed via SMTP (Gmail, using an App Password).
3. Clicking the link marks the email verified — the account is still inactive until an admin approves it.
4. An admin (identified by the `ADMIN_EMAILS` whitelist, not a DB role) activates the account and can grant `can_access_echo`/`can_access_emr` independently from the `/admin` panel.

See `CLAUDE.md` → Auth model for the exact file/route breakdown.

## Environment Variables

Set these in `.env` (see `app/config.py` for defaults):

```bash
# Flask
SECRET_KEY=
FLASK_ENV=development
FLASK_DEBUG=0

# HosXP Database Connection
HOSXP_HOST=
HOSXP_USER=
HOSXP_PASS=
HOSXP_DB=
HOSXP_PORT=3306

# Session Security
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax

# Base URL of this app (used to build the Google OAuth redirect + email links)
BASE_URL=http://localhost:5009

# Google OAuth (from Google Cloud Console — redirect URI must be
# ${BASE_URL}/auth/callback, registered exactly there)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Gmail account used to send email-verification links (use an App Password)
EMAIL_FROM=
EMAIL_PASSWORD=

# Admin whitelist (comma-separated emails)
ADMIN_EMAILS=

# Email verification token expiry, seconds (default 24h)
EMAIL_VERIFY_TOKEN_MAX_AGE=86400
```

## Security

- **CSRF**: All forms/JSON POSTs protected with Flask-WTF CSRF tokens (barcode scanner endpoints are the one exemption, since they're hit by a non-browser client)
- **SQL Injection**: Parameterized queries only; SQL lives in `sql/*.sql` files
- **Auth**: Google OAuth + email verification + admin approval gate every page/endpoint (see Auth Model above)
- **Secrets**: All credentials in `.env`, never hardcoded, never committed
