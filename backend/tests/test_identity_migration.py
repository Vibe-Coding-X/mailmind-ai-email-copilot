from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import Settings


ALLOWED_BUSINESS_TABLES = {"users", "auth_accounts", "sessions"}
FORBIDDEN_BUSINESS_TABLES = {
    "mailboxes",
    "mailbox_credentials",
    "emails",
    "daily_digests",
    "digest_items",
    "ai_runs",
    "user_actions",
    "sync_jobs",
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


def test_identity_migration_upgrades_and_downgrades() -> None:
    config = _alembic_config()

    command.downgrade(config, "base")
    command.upgrade(config, "head")

    assert _business_tables() == ALLOWED_BUSINESS_TABLES
    assert FORBIDDEN_BUSINESS_TABLES.isdisjoint(_business_tables())

    command.downgrade(config, "base")
    assert _business_tables() == set()

    command.upgrade(config, "head")
