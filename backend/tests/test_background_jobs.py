from app.core.config import Settings
from app.jobs.celery_app import create_celery_app
from app.jobs.tasks import health_check


def test_celery_app_uses_eager_mode_for_tests() -> None:
    celery_app = create_celery_app(
        Settings(
            redis_url="redis://localhost:6379/9",
            background_jobs_eager=True,
        )
    )

    assert celery_app.conf.broker_url == "redis://localhost:6379/9"
    assert celery_app.conf.result_backend == "redis://localhost:6379/9"
    assert celery_app.conf.task_always_eager is True
    assert celery_app.conf.task_eager_propagates is True


def test_health_check_task_runs_in_eager_mode() -> None:
    health_check.app.conf.task_always_eager = True
    health_check.app.conf.task_eager_propagates = True

    result = health_check.delay()

    assert result.get(timeout=1) == {"status": "ok", "worker": "mailmind"}
