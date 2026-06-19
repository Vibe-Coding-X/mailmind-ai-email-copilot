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


def test_user_action_migration_upgrades_and_downgrades() -> None:
    config = _alembic_config()

    command.downgrade(config, "base")
    command.upgrade(config, "head")

    assert _business_tables() == EXPECTED_BUSINESS_TABLES
    engine = create_engine(Settings().database_url, pool_pre_ping=True)
    try:
        inspector = inspect(engine)
        assert "user_actions" in inspector.get_table_names()
        columns = {column["name"] for column in inspector.get_columns("user_actions")}
        assert {
            "id",
            "user_id",
            "mailbox_id",
            "digest_id",
            "digest_item_id",
            "email_id",
            "action_type",
            "action_status",
            "source",
            "provider_effect",
            "before_state",
            "after_state",
            "error_code",
            "error_message",
            "created_at",
            "executed_at",
        } == columns
        checks = {
            check["name"]: check["sqltext"]
            for check in inspector.get_check_constraints("user_actions")
        }
        assert "mark_read" in checks["user_actions_action_type_check"]
        assert "executed" in checks["user_actions_action_status_check"]
        assert "gmail_synced" in checks["user_actions_provider_effect_check"]
        indexes = {index["name"] for index in inspector.get_indexes("user_actions")}
        assert "user_actions_user_created_idx" in indexes
        assert "user_actions_email_created_idx" in indexes
    finally:
        engine.dispose()

    command.downgrade(config, "20260619_0005")
    assert "user_actions" not in _business_tables()

    command.upgrade(config, "head")
