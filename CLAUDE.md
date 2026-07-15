# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## กฎเหล็ก — ห้ามเดา

ห้ามเดาหรือสมมติเจตนา/context ที่ไม่ชัดเจนเอาเอง ถ้าคำสั่ง/context ของผู้ใช้ไม่ชัด ไม่ครบ หรือตีความได้หลายแบบ — หรือไม่มั่นใจว่าเข้าใจถูกต้อง — ให้ถามผู้ใช้ก่อนลงมือทำ (แก้โค้ด, รัน command ที่มีผลกระทบ, หรือสรุปคำตอบ) ห้ามเดาแล้วเดินหน้าทำเลยโดยไม่ถาม

## Commands

```bash
# Install dependencies
uv sync

# Run dev server (Flask debug mode, port 5009)
uv run python main.py

# Run with Docker (production-like, gunicorn)
docker compose up --build -d

# Run tests
uv run pytest tests/

# Run a single test
uv run pytest tests/test_app.py::TestPerHNEndpoints::test_egfr_success_and_zfill
```

There is no configured linter/formatter in `pyproject.toml` — don't assume `ruff`/`black` are present unless added.

## Verification rule — required before claiming "test passed"

Whenever code is added or edited, you may NOT report "tests pass" / "ทดสอบผ่าน" based on `pytest` or static checks alone. You must verify it actually runs in Docker, end to end:

```bash
# 1. Build and start the container (rebuild image with latest code)
docker compose up --build -d

# 2. Remove leftover/unrelated dangling images from the rebuild
docker image prune -f

# 3. Confirm the container is actually up and healthy
docker compose ps

# 4. Exercise the app while it's running (hit real routes/endpoints, e.g.)
curl -i http://localhost:5009/   # expect 302 -> /login when unauth
# POST endpoints are CSRF-protected, so a tokenless POST returns 400 (CSRF missing) BEFORE the auth check:
curl -i -X POST http://localhost:5009/api/emr -H 'Content-Type: application/json' -d '{"hn":"123"}'  # expect 400 CSRF (not 401)
# To hit the auth gate itself, use a login-gated GET, e.g.:
curl -i http://localhost:5009/api/admin/users  # expect 403 unauth (admin-only)

# 5. Inspect logs for errors/tracebacks
docker compose logs web --tail=200
```

Only report success if **all** of the following hold — otherwise report exactly what failed:
- `docker compose up --build` completed without error.
- Dangling/unrelated images from the build were cleaned up (`docker image prune -f`).
- The container is running (not restarting/exited) and the exercised endpoint(s)/page(s) actually work.
- `docker compose logs` shows no errors/tracebacks/exceptions for the relevant request.

After verifying, **leave the container running** (`docker compose up -d`, `docker image prune -f` to clean up the old/unused image from the rebuild) — do NOT `docker compose down` afterward. This is a container project: the user wants to try the change live right after you finish, so it must stay up unless they explicitly ask you to stop it.

## Architecture

Flask app factory (`app/__init__.py:create_app`) wires together two blueprints registered in `app/api/__init__.py`:
- `api_bp` (mounted at `/api`) — JSON endpoints, split by concern across `app/api/routes_auth.py` (Google OAuth login/callback/logout, email verification), `routes_admin.py` (admin user management), `routes_search.py` (per-HN lookups), and `routes_barcode.py` (scanner + DB diagnostic).
- `views_bp` (`app/api/views.py`, mounted at `/`) — Jinja2 page rendering.

Both blueprints are populated purely by importing those route modules for their registration side effects — there's no other wiring. A new endpoint just needs a `@api_bp.route`/`@views_bp.route` decorator in the matching module, and (if it's a new module) an import line in `app/api/__init__.py`.

### Data flow: HosXP → UI (ad-hoc, no cache)

This app is a read-only reporting layer in front of a hospital information system (HosXP, a MySQL DB it does not own):

1. SQL lives in `sql/*.sql` files, read (and `@lru_cache`d) via `app/utils/sql_reader.py`.
2. `app/services/hosxp_service.py:execute_sql_on_hosxp` runs a query against HosXP (`app/models/connection.py:get_hosxp_connection`, a module-level singleton engine) with pandas and returns a DataFrame — no local caching. Used by every per-HN search endpoint.

There is no SQLite cache, sync job, scheduler, or dashboard of HosXP data — that machinery was removed once it was clear the dashboard was unused. Local state under `instance/` is `barcode_cache.json` (last scanned HN) plus `app.db` — a small SQLite DB, unrelated to HosXP caching, that stores the local user-accounts table for the auth system (see Auth model below).

### Per-HN search endpoints follow one pattern

`/api/egfr`, `/api/a1c`, `/api/inr`, `/api/consult`, `/api/flow_opd`, `/api/emr` in `app/api/routes_search.py` share the helper `_hn_search("<name>.sql", zfill=...)`: it validates `hn` is digits (zero-padded to 7 for most, but *not* `consult`/`flow_opd`, which pass `zfill=False`), runs the query, and serializes the DataFrame via `records_from_df` (`app/utils/helpers.py`) into `{status, columns, records, total}`. When adding a new lab/record type, add a one-liner that calls `_hn_search(...)` — do not re-inline the serialization. All of them require login (`@login_required`, see Auth model below). `/api/emr` is the one exception: instead of `login_required` it inlines an OR-flag check (either `can_access_echo` or `can_access_emr`), additionally fetches `emr_rx.sql`, and groups prescription rows by `VN` (visit number) onto each record as `rx_list`.

### Auth model

Real per-user accounts via Google OAuth, backed by a local SQLite DB (`instance/app.db`, separate from the HosXP MySQL connection) — see `app/models/user.py` (the `User` table: `email`, `google_sub`, `is_verified`, `is_active`, `can_access_echo`, `can_access_emr`, `totp_secret`, `totp_enabled`) and `app/models/local_db.py` (engine/session).

- **Login flow** (`app/api/routes_auth.py`): `/auth/login` redirects to Google via Authlib; `/auth/callback` upserts the `User` row by `google_sub` and sets `session["user_id"]`. On first login, an email-verification link (`itsdangerous`-signed, 24h expiry) is sent via SMTP (`app/utils/email.py`) to `/auth/verify-email/<token>`. Verifying the email is **not** sufficient — an admin must separately set `is_active = True` before the account can use anything.
- **TOTP 2FA is a mandatory third gate.** After a user is verified + active, `login_required` still redirects to `/auth/setup-2fa` (first time — shows a QR built with `pyotp`/`qrcode`, sets `totp_secret`, and flips `totp_enabled` on the first correct code) or `/auth/verify-2fa` (returning users) until `session["totp_verified"]` is set. The secret persists in the DB, but the `totp_verified` flag is per-session, so every new session re-prompts for a code. `/auth/logout` clears both `user_id` and `totp_verified`. There is **no** admin reset path — losing the authenticator means clearing `totp_secret`/`totp_enabled` in the DB by hand.
- **Admin panel** (`/admin` page + `/api/admin/users*` in `app/api/routes_admin.py`): admins are identified purely by an `ADMIN_EMAILS` whitelist in `.env` (no DB role column) so the very first admin can always get in — `admin_required` (in `app/utils/auth.py`) bypasses the verified/active gate entirely for whitelisted emails. Admins can activate/deactivate/delete any user and toggle their `can_access_echo`/`can_access_emr` flags independently (activating a user does not itself grant either).
- **The whole site requires login.** Every page in `views.py` (index, consult, flow_opd, egfr, a1c, inr) and every per-HN API endpoint in `routes_search.py` (except `/api/emr`, see below) is gated by `@login_required` (in `app/utils/auth.py`) — a logged-in, verified, active, **2FA-passed** user, no specific access flag needed beyond that.
- **`/echo` and `/emr` pages** additionally require a specific flag, gated by `access_required("can_access_echo"/"can_access_emr")`.
- **`/api/emr` is PHI** and enforces this at the API level too — it accepts *either* `can_access_echo` or `can_access_emr` (the `/echo` integrated view also reads EMR), checked inline via `get_current_user()` rather than through `access_required` (which only checks one flag).

CSRF protection (Flask-WTF) is applied globally except where explicitly exempted; endpoints hit by non-browser clients (barcode scanner in `routes_barcode.py`) are exempted.

### Config

All runtime config comes from `.env` via `app/config.py:Config` (loaded once with `load_dotenv()`). There is no separate dev/prod config class — behavior differences (e.g. `DEBUG`, `SESSION_COOKIE_SECURE`) are env-var-driven flags on the single `Config` class. Auth-related vars: `BASE_URL` (derives `GOOGLE_REDIRECT_URI` as `{BASE_URL}/auth/callback` — must match what's registered in Google Cloud Console exactly, including scheme; Google requires HTTPS for any non-`localhost` redirect URI), `GOOGLE_CLIENT_ID`/`GOOGLE_CLIENT_SECRET`, `EMAIL_FROM`/`EMAIL_PASSWORD` (Gmail SMTP, hardcoded to `smtp.gmail.com:587` in `app/utils/email.py` — spaces in a pasted Gmail App Password are stripped automatically), `ADMIN_EMAILS`, `EMAIL_VERIFY_TOKEN_MAX_AGE`.

### Frontend

No JS build step / framework — plain JS per page under `static/js/pages/*.js` (one file per route, matching `templates/pages/*.html`), a shared `static/js/api.js` API client, and `static/js/utils.js` helpers. CSS is similarly split into `main.css`/`theme.css` plus per-page files under `static/css/pages/`. Cache-busting for static assets is automatic via file mtime (see `_register_cache_busting` in `app/__init__.py`) — no manual versioning needed when editing JS/CSS.

Templates in `templates/pages/*.html` correspond 1:1 with `views.py` routes and `static/js/pages/*.js` client logic for that page.
