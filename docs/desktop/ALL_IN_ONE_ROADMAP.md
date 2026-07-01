# MailMind All-in-one Desktop Roadmap

## Why v0.7.0 is Shell-only

The current MailMind architecture depends on:

- **FastAPI** (Python 3.11+) — API server
- **PostgreSQL 15** — primary database
- **Redis 7** — cache and Celery broker
- **Celery** — background job processing

Bundling all four into a single desktop installer would result in:

- 300MB+ installer size
- 5+ concurrent processes
- Complex startup/shutdown orchestration
- Platform-specific PostgreSQL/Redis packaging
- Difficult upgrade and migration paths

v0.7.0 avoids these costs by being a thin Electron shell that connects to locally running services.

## Roadmap

### v0.7.0 — Desktop Shell ✅

- Electron wrapper for the web app
- Health check and fallback screen
- electron-builder packaging (Windows / macOS / Linux)
- GitHub Actions auto-build
- No embedded runtime

### v0.7.1 — Release Pipeline ✅

- Stable GitHub Actions pipeline for Windows / macOS / Linux
- Verified installer generation on all three platforms
- Tag-triggered GitHub Release draft with packaged artifacts
- Clear artifact expectations (`.zip` download containing platform installer)

### v0.7.2 — Desktop UX

- System tray support
- Window size / position persistence
- Better desktop menus
- Desktop notifications for connection state
- Close-to-tray behavior

### v0.7.3 — Config & Diagnostics

- Connection diagnostics screen
- Config editor for app URL and health URL
- Desktop log files and log directory shortcut
- Copyable diagnostics bundle for bug reports

### v0.7.4 — Local Runtime Preview

- Bundle a Python embeddable distribution
- FastAPI starts as a child process of Electron
- SQLite replaces PostgreSQL for single-user mode
- APScheduler replaces Celery + Redis
- User data stored in `app.getPath("userData")`
- Still no auto-update or OAuth deep links

### v0.8.0 — All-in-one Desktop App

- Full offline capability
- Auto-update via electron-updater
- OAuth deep links (`mailmind://` protocol)
- Code signing (Windows EV + macOS notarization)
- System tray and background sync
- Attachment download and caching
- Single-email AI summaries
- Reply drafting

## Technical Decisions Needed

| Decision | Options |
|---|---|
| Embedded Python | python-embed vs PyInstaller vs Nuitka |
| Local database | SQLite vs DuckDB vs embedded PostgreSQL |
| Job queue | APScheduler vs asyncio tasks vs RQ |
| OAuth callback | localhost redirect vs custom protocol vs loopback |
| Migration strategy | Alembic dual-dialect vs separate migration path |
