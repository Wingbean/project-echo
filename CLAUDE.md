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
curl -i http://localhost:5009/
curl -i -X POST http://localhost:5009/api/emr -H 'Content-Type: application/json' -d '{"hn":"123"}'  # expect 401 unauth

# 5. Inspect logs for errors/tracebacks
docker compose logs web --tail=200
```

Only report success if **all** of the following hold — otherwise report exactly what failed:
- `docker compose up --build` completed without error.
- Dangling/unrelated images from the build were cleaned up (`docker image prune -f`).
- The container is running (not restarting/exited) and the exercised endpoint(s)/page(s) actually work.
- `docker compose logs` shows no errors/tracebacks/exceptions for the relevant request.

After verifying, tear down or leave running per the user's preference — don't leave stray containers around silently.

## Architecture

Flask app factory (`app/__init__.py:create_app`) wires together two blueprints registered in `app/api/__init__.py`:
- `api_bp` (mounted at `/api`) — JSON endpoints, split by concern across `app/api/routes_auth.py` (secret-code verify), `routes_search.py` (per-HN lookups), and `routes_barcode.py` (scanner + DB diagnostic).
- `views_bp` (`app/api/views.py`, mounted at `/`) — Jinja2 page rendering.

Both blueprints are populated purely by importing those route modules for their registration side effects — there's no other wiring. A new endpoint just needs a `@api_bp.route`/`@views_bp.route` decorator in the matching module, and (if it's a new module) an import line in `app/api/__init__.py`.

### Data flow: HosXP → UI (ad-hoc, no cache)

This app is a read-only reporting layer in front of a hospital information system (HosXP, a MySQL DB it does not own):

1. SQL lives in `sql/*.sql` files, read (and `@lru_cache`d) via `app/utils/sql_reader.py`.
2. `app/services/hosxp_service.py:execute_sql_on_hosxp` runs a query against HosXP (`app/models/connection.py:get_hosxp_connection`, a module-level singleton engine) with pandas and returns a DataFrame — no local caching. Used by every per-HN search endpoint.

There is no SQLite cache, sync job, scheduler, or dashboard — that machinery was removed once it was clear the dashboard was unused. The only local state under `instance/` is `barcode_cache.json` (last scanned HN).

### Per-HN search endpoints follow one pattern

`/api/egfr`, `/api/a1c`, `/api/inr`, `/api/consult`, `/api/flow_opd`, `/api/emr` in `app/api/routes_search.py` share the helper `_hn_search("<name>.sql", zfill=...)`: it validates `hn` is digits (zero-padded to 7 for most, but *not* `consult`/`flow_opd`, which pass `zfill=False`), runs the query, and serializes the DataFrame via `records_from_df` (`app/utils/helpers.py`) into `{status, columns, records, total}`. When adding a new lab/record type, add a one-liner that calls `_hn_search(...)` — do not re-inline the serialization. `/api/emr` is the one exception: it requires auth, additionally fetches `emr_rx.sql`, and groups prescription rows by `VN` (visit number) onto each record as `rx_list`.

### Auth model

Session-cookie based (no user accounts), all secret-code driven:
- **Secret code pages** (`/echo`, `/emr`): a single shared `ECHO_SECRET_CODE` sets `session["echo_authenticated"]` / `session["emr_authenticated"]` via `_verify_secret_code` in `routes_auth.py` (constant-time `hmac.compare_digest`).
- **`/api/emr` is PHI** and enforces this at the API level too — it requires `emr_authenticated` *or* `echo_authenticated` (the `/echo` integrated view also reads EMR). The other per-HN endpoints are intentionally open (their pages are public).

CSRF protection (Flask-WTF) is applied globally except where explicitly exempted; endpoints hit by non-browser clients (barcode scanner in `routes_barcode.py`) are exempted.

### Config

All runtime config comes from `.env` via `app/config.py:Config` (loaded once with `load_dotenv()`). There is no separate dev/prod config class — behavior differences (e.g. `DEBUG`, `SESSION_COOKIE_SECURE`) are env-var-driven flags on the single `Config` class.

### Frontend

No JS build step / framework — plain JS per page under `static/js/pages/*.js` (one file per route, matching `templates/pages/*.html`), a shared `static/js/api.js` API client, and `static/js/utils.js` helpers. CSS is similarly split into `main.css`/`theme.css` plus per-page files under `static/css/pages/`. Cache-busting for static assets is automatic via file mtime (see `_register_cache_busting` in `app/__init__.py`) — no manual versioning needed when editing JS/CSS.

Templates in `templates/pages/*.html` correspond 1:1 with `views.py` routes and `static/js/pages/*.js` client logic for that page.
