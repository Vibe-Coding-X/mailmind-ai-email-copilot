from __future__ import annotations

import os

from celery import Celery

from app.core.config import Settings, get_settings


def default_worker_pool() -> str | None:
    if os.name == "nt":
        return "solo"
    return None


def create_celery_app(settings: Settings | None = None) -> Celery:
    resolved_settings = settings or get_settings()
    worker_pool = default_worker_pool()
    celery_app = Celery(
        "mailmind",
        broker=resolved_settings.celery_broker_url,
        backend=resolved_settings.celery_result_backend,
        include=["app.jobs.tasks"],
    )
    config = {
        "task_default_queue": "mailmind",
        "task_serializer": "json",
        "result_serializer": "json",
        "accept_content": ["json"],
        "timezone": "UTC",
        "enable_utc": True,
        "task_always_eager": resolved_settings.background_jobs_eager,
        "task_eager_propagates": resolved_settings.background_jobs_eager,
        "broker_connection_retry_on_startup": True,
        "worker_prefetch_multiplier": 1,
    }
    if worker_pool is not None:
        config["worker_pool"] = worker_pool
    celery_app.conf.update(**config)
    return celery_app


celery_app = create_celery_app()

