from app.db import models  # noqa: F401
from app.db.base import Base


IDENTITY_TABLES = {"users", "auth_accounts", "sessions"}
MAILBOX_FOUNDATION_TABLES = {"mailboxes", "mailbox_credentials"}
FORBIDDEN_LATER_PHASE_TABLES = {
    "daily_digests",
    "digest_items",
    "ai_runs",
    "user_actions",
}


def test_identity_tables_are_registered_in_metadata() -> None:
    assert IDENTITY_TABLES.issubset(Base.metadata.tables.keys())


def test_mailbox_foundation_tables_are_registered_in_metadata() -> None:
    assert MAILBOX_FOUNDATION_TABLES.issubset(Base.metadata.tables.keys())


def test_email_sync_tables_are_registered_in_metadata() -> None:
    assert {"emails", "sync_jobs"}.issubset(Base.metadata.tables.keys())


def test_later_phase_business_tables_are_not_registered_in_metadata() -> None:
    assert FORBIDDEN_LATER_PHASE_TABLES.isdisjoint(Base.metadata.tables.keys())


def test_users_email_has_unique_constraint() -> None:
    users = Base.metadata.tables["users"]

    assert users.c.email.unique is True or any(
        {column.name for column in constraint.columns} == {"email"}
        for constraint in users.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )


def test_auth_accounts_user_id_references_users() -> None:
    auth_accounts = Base.metadata.tables["auth_accounts"]

    foreign_keys = {fk.target_fullname for fk in auth_accounts.c.user_id.foreign_keys}

    assert foreign_keys == {"users.id"}


def test_sessions_user_id_references_users() -> None:
    sessions = Base.metadata.tables["sessions"]

    foreign_keys = {fk.target_fullname for fk in sessions.c.user_id.foreign_keys}

    assert foreign_keys == {"users.id"}
