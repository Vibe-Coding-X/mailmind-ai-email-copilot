# MailMind Desktop Shell

## Overview

MailMind Desktop is an **Electron shell** that wraps the existing MailMind web application. It does not embed the backend, database, or job queue. The desktop app connects to locally running MailMind services.

## Positioning

| Version | Scope |
|---|---|
| v0.7.0 | Desktop Shell (Electron wrapper) |
| v0.8.0 | Local Runtime Preview (embedded Python) |
| v0.9.0 | Embedded DB Prototype (SQLite) |
| v1.0.0 | All-in-one Desktop App |

## Prerequisites

Before launching the desktop app, start the MailMind services locally:

```bash
# 1. Backend (FastAPI)
cd backend
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 2. Frontend (Next.js)
cd frontend
npm install
npm run dev

# 3. Optional: Celery worker
cd backend
uv run celery -A app.jobs.celery_app worker --loglevel=info --pool=solo
```

## Development

```bash
cd desktop
npm install
npm run dev
```

This starts Electron in development mode. The app loads `http://127.0.0.1:3000` by default.

## Default URLs

| Purpose | Default | Environment Variable |
|---|---|---|
| Web App | `http://127.0.0.1:3000` | `MAILMIND_DESKTOP_APP_URL` |
| API Health | `http://127.0.0.1:8000/health` | `MAILMIND_DESKTOP_API_HEALTH_URL` |

Override via environment variables or place a `config.json` in the Electron `userData` directory.

## Configuration Priority

1. Environment variables
2. `<userData>/config.json` (Electron `app.getPath("userData")`)
3. Built-in defaults

## Current Limitations

- Requires locally running backend and frontend
- No embedded database or job queue
- No OAuth deep links
- No auto-update
- No system tray
- Unsigned builds (SmartScreen / Gatekeeper warnings expected)
