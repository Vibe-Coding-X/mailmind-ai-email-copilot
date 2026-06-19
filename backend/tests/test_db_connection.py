from sqlalchemy import inspect, text

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine_from_settings, session_scope


def test_base_metadata_contains_only_current_phase_business_tables() -> None:
    current_phase_business_tables = {"mailboxes", "mailbox_credentials"}
    later_phase_business_tables = {
        "emails",
        "daily_digests",
        "digest_items",
        "ai_runs",
        "user_actions",
        "sync_jobs",
    }

    assert current_phase_business_tables.issubset(Base.metadata.tables.keys())
    assert later_phase_business_tables.isdisjoint(Base.metadata.tables.keys())


def test_database_connection_uses_configured_database_url() -> None:
    settings = Settings()
    engine = create_engine_from_settings(settings)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

    table_names = set(inspect(engine).get_table_names())
    assert table_names <= {
        "alembic_version",
        "users",
        "auth_accounts",
        "sessions",
        "mailboxes",
        "mailbox_credentials",
    }


def test_session_scope_can_execute_simple_query() -> None:
    settings = Settings()
    engine = create_engine_from_settings(settings)

    with session_scope(engine) as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
