from sqlalchemy import inspect, text

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine_from_settings, session_scope


def test_base_metadata_starts_without_business_tables() -> None:
    assert Base.metadata.tables == {}


def test_database_connection_uses_configured_database_url() -> None:
    settings = Settings()
    engine = create_engine_from_settings(settings)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT 1")).scalar_one() == 1

    assert inspect(engine).get_table_names() == []


def test_session_scope_can_execute_simple_query() -> None:
    settings = Settings()
    engine = create_engine_from_settings(settings)

    with session_scope(engine) as session:
        assert session.execute(text("SELECT 1")).scalar_one() == 1
