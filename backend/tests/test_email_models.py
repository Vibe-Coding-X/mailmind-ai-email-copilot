from app.db import models  # noqa: F401
from app.db.base import Base


EMAIL_SYNC_TABLES = {"emails", "sync_jobs"}
FORBIDDEN_LATER_PHASE_TABLES = {
    "daily_digests",
    "digest_items",
    "ai_runs",
    "user_actions",
}


def test_email_sync_tables_are_registered_in_metadata() -> None:
    assert EMAIL_SYNC_TABLES.issubset(Base.metadata.tables.keys())


def test_later_digest_ai_and_action_tables_are_not_registered() -> None:
    assert FORBIDDEN_LATER_PHASE_TABLES.isdisjoint(Base.metadata.tables.keys())


def test_emails_columns_and_constraints_match_database_design() -> None:
    emails = Base.metadata.tables["emails"]

    expected_columns = {
        "id",
        "user_id",
        "mailbox_id",
        "provider",
        "external_id",
        "external_thread_id",
        "internet_message_id",
        "subject",
        "from_name",
        "from_address",
        "to_addresses",
        "cc_addresses",
        "snippet",
        "body_text",
        "body_text_truncated",
        "received_at",
        "is_read",
        "provider_labels",
        "gmail_history_id",
        "first_synced_at",
        "last_synced_at",
        "created_at",
        "updated_at",
    }

    assert expected_columns.issubset(emails.c.keys())
    assert {fk.target_fullname for fk in emails.c.user_id.foreign_keys} == {"users.id"}
    assert {fk.target_fullname for fk in emails.c.mailbox_id.foreign_keys} == {
        "mailboxes.id"
    }
    assert any(
        {column.name for column in constraint.columns} == {"mailbox_id", "external_id"}
        for constraint in emails.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )


def test_sync_jobs_columns_and_constraints_match_database_design() -> None:
    sync_jobs = Base.metadata.tables["sync_jobs"]

    expected_columns = {
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

    assert expected_columns.issubset(sync_jobs.c.keys())
    assert {fk.target_fullname for fk in sync_jobs.c.user_id.foreign_keys} == {"users.id"}
    assert {fk.target_fullname for fk in sync_jobs.c.mailbox_id.foreign_keys} == {
        "mailboxes.id"
    }
    assert any(
        {column.name for column in constraint.columns} == {"celery_task_id"}
        for constraint in sync_jobs.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )
