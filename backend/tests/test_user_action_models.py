from app.db import models  # noqa: F401
from app.db.base import Base


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


def test_user_actions_table_is_registered_in_metadata() -> None:
    assert "user_actions" in Base.metadata.tables
    assert set(Base.metadata.tables.keys()) == EXPECTED_BUSINESS_TABLES


def test_user_actions_columns_and_constraints_match_database_design() -> None:
    user_actions = Base.metadata.tables["user_actions"]

    assert set(user_actions.c.keys()) == {
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
    }
    assert {fk.target_fullname for fk in user_actions.c.user_id.foreign_keys} == {
        "users.id"
    }
    assert {fk.target_fullname for fk in user_actions.c.mailbox_id.foreign_keys} == {
        "mailboxes.id"
    }
    assert {fk.target_fullname for fk in user_actions.c.digest_id.foreign_keys} == {
        "daily_digests.id"
    }
    assert {fk.target_fullname for fk in user_actions.c.digest_item_id.foreign_keys} == {
        "digest_items.id"
    }
    assert {fk.target_fullname for fk in user_actions.c.email_id.foreign_keys} == {
        "emails.id"
    }
    assert any(index.name == "user_actions_user_created_idx" for index in user_actions.indexes)
    assert any(
        index.name == "user_actions_digest_item_created_idx"
        for index in user_actions.indexes
    )
    assert any(index.name == "user_actions_email_created_idx" for index in user_actions.indexes)
    assert any(
        index.name == "user_actions_status_created_idx" for index in user_actions.indexes
    )
