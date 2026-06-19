from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import Settings


EXPECTED_BUSINESS_TABLES = {
    "users",
    "auth_accounts",
    "sessions",
    "mailboxes",
    "mailbox_credentials",
    "emails",
    "sync_jobs",
    "daily_digests",
    "digest_items",
    "ai_runs",
    "user_actions",
}
EXPECTED_SYNC_JOB_COLUMNS = {
    "id",
    "user_id",
    "mailbox_id",
    "digest_id",
    "celery_task_id",
    "job_type",
    "trigger_source",
    "job_key",
    "target_date",
    "status",
    "retry_count",
    "payload_json",
    "error_code",
    "error_message",
    "created_at",
    "started_at",
    "finished_at",
}


def _alembic_config() -> Config:
    return Config("alembic.ini")


def _business_tables() -> set[str]:
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    try:
        table_names = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    return table_names - {"alembic_version"}


def test_email_sync_migration_upgrades_and_downgrades() -> None:
    config = _alembic_config()

    command.downgrade(config, "base")
    command.upgrade(config, "head")

    assert _business_tables() == EXPECTED_BUSINESS_TABLES
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    try:
        inspector = inspect(engine)
        assert {
            column["name"] for column in inspector.get_columns("sync_jobs")
        } == EXPECTED_SYNC_JOB_COLUMNS
        checks = {
            check["name"]: check["sqltext"]
            for check in inspector.get_check_constraints("sync_jobs")
        }
        assert "generate_daily_digest" in checks["sync_jobs_job_type_check"]
        assert "refresh_daily_digest" in checks["sync_jobs_job_type_check"]
        assert "sync_jobs_mailbox_created_idx" in {
            index["name"] for index in inspector.get_indexes("sync_jobs")
        }
        assert "sync_jobs_digest_created_idx" in {
            index["name"] for index in inspector.get_indexes("sync_jobs")
        }
    finally:
        engine.dispose()

    command.downgrade(config, "20260619_0002")
    assert "emails" not in _business_tables()
    assert "sync_jobs" not in _business_tables()

    command.upgrade(config, "head")
