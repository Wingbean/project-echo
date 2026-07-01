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
uv run pytest tests/test_app.py::TestAPIRoutes::test_sync_without_pin
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
curl -i http://localhost:5009/api/dashboard-data

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
- `api_bp` (`app/api/routes.py`, mounted at `/api`) — JSON endpoints.
- `views_bp` (`app/api/views.py`, mounted at `/`) — Jinja2 page rendering.

Both blueprints are populated purely by importing `routes` and `views` for their route-registration side effects — there's no other wiring, so a new endpoint just needs a `@api_bp.route` or `@views_bp.route` decorator in the corresponding file.

### Data flow: HosXP → SQLite cache → UI

This app is a read-mostly reporting layer in front of a hospital information system (HosXP, a MySQL DB it does not own):

1. SQL lives in `sql/*.sql` files, read via `app/utils/sql_reader.py`.
2. `app/services/hosxp_service.py` runs those queries against HosXP (`app/models/connection.py:get_hosxp_connection`) with pandas, and either:
   - **caches** results into the local SQLite `instance/data_cache.db` (`sync_data_from_hosxp`, used for dashboard/bulk data), or
   - **executes ad-hoc** and returns a DataFrame directly without caching (`execute_sql_on_hosxp`, used by per-HN search endpoints like `/api/egfr`, `/api/a1c`, `/api/inr`, `/api/emr`, `/api/consult`, `/api/flow_opd`).
3. `app/services/render_service.py` reads the SQLite cache back out for dashboard/table display.
4. `app/services/scheduler_service.py` runs `sync_data_from_hosxp` on a fixed daily schedule (08:00/12:00/16:00) in a background thread started from `create_app`.

Two separate file locks under `instance/` guard against duplicate work across gunicorn workers: `scheduler.lock` (only one worker starts the scheduler thread) and `data_cache.sync.lock` (only one sync runs at a time). Sync progress/results are polled via a JSON file (`instance/sync_status.json`), not held in memory, since gunicorn workers don't share process state — `/api/sync` starts a background thread and returns immediately, `/api/sync-status` reads the file.

### Per-HN search endpoints follow one pattern

`/api/egfr`, `/api/a1c`, `/api/inr`, `/api/emr`, `/api/consult`, `/api/flow_opd` in `app/api/routes.py` are all built the same way: validate `hn` is digits (zero-padded to 7 for most, but *not* `consult`/`flow_opd`), call `execute_sql_on_hosxp("<name>.sql", params={"hn": hn})`, `fillna("")`, then manually convert pandas Timedelta/Timestamp/NaT values to JSON-safe strings before returning `{status, columns, records, total}`. When adding a new lab/record type, copy this pattern rather than inventing a new response shape. `/api/emr` additionally fetches `emr_rx.sql` and groups prescription rows by `VN` (visit number) onto each record as `rx_list`.

### Auth model

Two independent auth schemes, both session-cookie based (no user accounts):
- **Secret code pages** (`/echo`, `/emr`): a single shared code per page (`ECHO_SECRET_CODE`, checked via a shared page's own code) sets `session["echo_authenticated"]` / `session["emr_authenticated"]`. See `_verify_secret_code` in `routes.py`.
- **Sync endpoints** (`/api/sync`, `/api/sync-auto`): PIN passed via `X-Sync-Pin` header, checked against `Config.SYNC_PIN`, not session-based, and CSRF-exempt (see `@csrf.exempt` throughout `routes.py` on GET-based/external-facing endpoints).

CSRF protection (Flask-WTF) is applied globally except where explicitly exempted; endpoints hit by non-browser clients (barcode scanner, polling) are exempted.

### Config

All runtime config comes from `.env` via `app/config.py:Config` (loaded once with `load_dotenv()`). There is no separate dev/prod config class — behavior differences (e.g. `DEBUG`, `SESSION_COOKIE_SECURE`) are env-var-driven flags on the single `Config` class.

### Frontend

No JS build step / framework — plain JS per page under `static/js/pages/*.js` (one file per route, matching `templates/pages/*.html`), a shared `static/js/api.js` API client, and `static/js/utils.js` helpers. CSS is similarly split into `main.css`/`theme.css` plus per-page files under `static/css/pages/`. Cache-busting for static assets is automatic via file mtime (see `_register_cache_busting` in `app/__init__.py`) — no manual versioning needed when editing JS/CSS.

Templates in `templates/pages/*.html` correspond 1:1 with `views.py` routes and `static/js/pages/*.js` client logic for that page.
