from app.db import models  # noqa: F401
from app.db.base import Base


MAILBOX_TABLES = {"mailboxes", "mailbox_credentials"}
FORBIDDEN_LATER_PHASE_TABLES = {
    "emails",
    "daily_digests",
    "digest_items",
    "ai_runs",
    "user_actions",
    "sync_jobs",
}


def test_mailbox_tables_are_registered_in_metadata() -> None:
    assert MAILBOX_TABLES.issubset(Base.metadata.tables.keys())


def test_later_phase_tables_are_not_registered_in_metadata() -> None:
    assert FORBIDDEN_LATER_PHASE_TABLES.isdisjoint(Base.metadata.tables.keys())


def test_mailboxes_columns_match_database_design_foundation() -> None:
    mailboxes = Base.metadata.tables["mailboxes"]

    expected_columns = {
        "id",
        "user_id",
        "provider",
        "provider_account_id",
        "email_address",
        "display_name",
        "permission_mode",
        "granted_scopes",
        "status",
        "last_sync_at",
        "last_successful_sync_at",
        "last_history_id",
        "sync_cursor",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(mailboxes.c.keys())
    assert {fk.target_fullname for fk in mailboxes.c.user_id.foreign_keys} == {"users.id"}


def test_mailbox_credentials_columns_match_database_design_foundation() -> None:
    credentials = Base.metadata.tables["mailbox_credentials"]

    expected_columns = {
        "mailbox_id",
        "credential_type",
        "refresh_token_encrypted",
        "imap_password_encrypted",
        "scopes_snapshot",
        "credentials_json",
        "encryption_key_version",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(credentials.c.keys())
    assert {fk.target_fullname for fk in credentials.c.mailbox_id.foreign_keys} == {
        "mailboxes.id"
    }
