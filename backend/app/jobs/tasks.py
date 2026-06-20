from __future__ import annotations

from app.jobs.celery_app import celery_app


@celery_app.task(name="app.jobs.health_check")
def health_check() -> dict[str, str]:
    return {"status": "ok", "worker": "mailmind"}

