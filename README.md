# Project Echo 📡

ระบบเว็บแอปพลิเคชันสำหรับจัดการและแสดงผลข้อมูล

## Features

- 🔄 **Data Sync** — ดึงข้อมูลจาก HosXP (MySQL) มาเก็บใน SQLite cache
- 📊 **Data Display** — แสดงผลข้อมูลในรูปแบบตาราง พร้อมค้นหาและกรอง
- 🔒 **Security** — CSRF protection, SQL injection prevention, PIN authentication
- 🌙 **Dark Mode** — รองรับธีมสว่าง/มืด
- 🇹🇭 **Thai Support** — รองรับภาษาไทยเต็มรูปแบบ (Noto Sans Thai)
- 📱 **Responsive** — ใช้งานได้ทุกอุปกรณ์

## Tech Stack

| Component       | Technology                     |
| --------------- | ------------------------------ |
| Backend         | Python + Flask                 |
| Template        | Jinja2                         |
| Frontend        | HTML, CSS, JavaScript          |
| Database        | SQLite (cache) + MySQL (HosXP) |
| Package Manager | uv                             |
| Container       | Docker + Gunicorn              |

## Quick Start

### 1. Setup Environment

```bash
# Copy and edit environment variables
cp .env.example .env
# Edit .env with your actual values
```

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
│   ├── __init__.py         # App factory + CSRF
│   ├── config.py           # Configuration from .env
│   ├── api/                # API routes + page views
│   ├── models/             # Database connections
│   ├── services/           # Business logic
│   └── utils/              # Helpers & validators
├── templates/              # Jinja2 templates
│   ├── base.html           # Base layout
│   ├── components/         # Reusable components
│   └── pages/              # Page templates
├── static/                 # CSS, JS, assets
│   ├── css/                # Theme + main + components
│   └── js/                 # API client + utilities
├── sql/                    # SQL scripts
├── tests/                  # Test suite
├── Dockerfile              # Container config
├── docker-compose.yml      # Docker Compose
├── gunicorn.conf.py        # Gunicorn settings
└── pyproject.toml          # uv dependencies
```

## Data Flow

```
SQL Files (sql/) → hosxp_service → HosXP MySQL Server
                                  ↓
                          pandas DataFrame
                                  ↓
                     SQLite cache (instance/data_cache.db)
                                  ↓
                         render_service
                                  ↓
                       Jinja2 Templates → Browser
```

## API Endpoints

| Method | Endpoint              | Description                           |
| ------ | --------------------- | ------------------------------------- |
| GET    | `/api/sync`           | Trigger full data sync (requires PIN) |
| GET    | `/api/sync-auto`      | Trigger auto sync (requires PIN)      |
| GET    | `/api/sync-status`    | Check sync status                     |
| GET    | `/api/dashboard-data` | Get all cached data                   |
| GET    | `/api/table/<name>`   | Get specific table data               |
| POST   | `/api/query`          | Query cached data                     |
| GET    | `/api/test-db`        | Test HosXP connection                 |

## Security

- **CSRF**: All forms protected with Flask-WTF CSRF tokens
- **SQL Injection**: Parameterized queries only; table names validated
- **Secrets**: All credentials in `.env`, never hardcoded
- **Sync Auth**: PIN-based authentication for sync operations
