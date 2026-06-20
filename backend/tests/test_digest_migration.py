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


def _alembic_config() -> Config:
    return Config("alembic.ini")


def _business_tables() -> set[str]:
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    try:
        table_names = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    return table_names - {"alembic_version"}


def test_digest_migration_upgrades_and_downgrades() -> None:
    config = _alembic_config()

    command.downgrade(config, "base")
    command.upgrade(config, "head")

    assert _business_tables() == EXPECTED_BUSINESS_TABLES
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    try:
        inspector = inspect(engine)
        assert "daily_digests" in inspector.get_table_names()
        assert "digest_items" in inspector.get_table_names()
        assert "ai_runs" in inspector.get_table_names()
        assert "user_actions" in inspector.get_table_names()
        assert "digest_id" in {
            column["name"] for column in inspector.get_columns("sync_jobs")
        }
        sync_indexes = {index["name"] for index in inspector.get_indexes("sync_jobs")}
        assert "sync_jobs_digest_created_idx" in sync_indexes
        checks = {
            check["name"]: check["sqltext"]
            for check in inspector.get_check_constraints("sync_jobs")
        }
        assert "generate_daily_digest" in checks["sync_jobs_job_type_check"]
        assert "refresh_daily_digest" in checks["sync_jobs_job_type_check"]
        assert {"provider_id", "provider_type"}.issubset(
            {column["name"] for column in inspector.get_columns("ai_runs")}
        )
    finally:
        engine.dispose()

    command.downgrade(config, "20260619_0004")
    assert _business_tables() == {
        "users",
        "auth_accounts",
        "sessions",
        "mailboxes",
        "mailbox_credentials",
        "emails",
        "sync_jobs",
    }
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    try:
        inspector = inspect(engine)
        assert "digest_id" not in {
            column["name"] for column in inspector.get_columns("sync_jobs")
        }
        checks = {
            check["name"]: check["sqltext"]
            for check in inspector.get_check_constraints("sync_jobs")
        }
        assert checks["sync_jobs_job_type_check"] == (
            "job_type::text = 'sync_today_emails'::text"
        )
    finally:
        engine.dispose()

    command.upgrade(config, "head")
