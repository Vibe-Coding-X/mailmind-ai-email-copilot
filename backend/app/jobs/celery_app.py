from __future__ import annotations

from celery import Celery

from app.core.config import Settings, get_settings


def create_celery_app(settings: Settings | None = None) -> Celery:
    resolved_settings = settings or get_settings()
    celery_app = Celery(
        "mailmind",
        broker=resolved_settings.celery_broker_url,
        backend=resolved_settings.celery_result_backend,
        include=["app.jobs.tasks"],
    )
    celery_app.conf.update(
        task_default_queue="mailmind",
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_always_eager=resolved_settings.background_jobs_eager,
        task_eager_propagates=resolved_settings.background_jobs_eager,
        broker_connection_retry_on_startup=True,
    )
    return celery_app


celery_app = create_celery_app()

