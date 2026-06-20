from app.db import models  # noqa: F401
from app.db.base import Base


DIGEST_TABLES = {"daily_digests", "digest_items", "ai_runs"}
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


def test_digest_tables_are_registered_in_metadata() -> None:
    assert DIGEST_TABLES.issubset(Base.metadata.tables.keys())
    assert "user_actions" in Base.metadata.tables


def test_metadata_contains_digest_business_tables_with_actions() -> None:
    assert set(Base.metadata.tables.keys()) == EXPECTED_BUSINESS_TABLES


def test_daily_digests_columns_and_constraints_match_database_design() -> None:
    daily_digests = Base.metadata.tables["daily_digests"]

    assert set(daily_digests.c.keys()) == {
        "id",
        "user_id",
        "mailbox_id",
        "digest_date",
        "version",
        "is_current",
        "status",
        "trigger_source",
        "generation_started_at",
        "generated_at",
        "coverage_start",
        "coverage_end",
        "mail_count",
        "new_mail_count_after_digest",
        "overview_json",
        "created_at",
        "updated_at",
    }
    assert {fk.target_fullname for fk in daily_digests.c.user_id.foreign_keys} == {
        "users.id"
    }
    assert {fk.target_fullname for fk in daily_digests.c.mailbox_id.foreign_keys} == {
        "mailboxes.id"
    }
    assert any(
        {column.name for column in constraint.columns}
        == {"mailbox_id", "digest_date", "version"}
        for constraint in daily_digests.constraints
        if constraint.__class__.__name__ == "UniqueConstraint"
    )
    assert any(index.name == "daily_digests_current_uq" for index in daily_digests.indexes)


def test_digest_items_columns_and_constraints_match_database_design() -> None:
    digest_items = Base.metadata.tables["digest_items"]

    assert set(digest_items.c.keys()) == {
        "id",
        "digest_id",
        "user_id",
        "mailbox_id",
        "email_id",
        "item_type",
        "section",
        "title",
        "summary",
        "category",
        "suggested_action",
        "priority",
        "reason",
        "deadline",
        "confidence",
        "display_order",
        "created_at",
        "updated_at",
    }
    assert {fk.target_fullname for fk in digest_items.c.digest_id.foreign_keys} == {
        "daily_digests.id"
    }
    assert {fk.target_fullname for fk in digest_items.c.email_id.foreign_keys} == {
        "emails.id"
    }
    assert any(index.name == "digest_items_email_current_uq" for index in digest_items.indexes)


def test_ai_runs_columns_and_constraints_match_database_design() -> None:
    ai_runs = Base.metadata.tables["ai_runs"]

    assert set(ai_runs.c.keys()) == {
        "id",
        "user_id",
        "mailbox_id",
        "digest_id",
        "run_type",
        "trigger_source",
        "provider_id",
        "provider_type",
        "model_provider",
        "model_name",
        "prompt_version",
        "output_schema_version",
        "input_hash",
        "input_summary_json",
        "output_json",
        "status",
        "error_code",
        "error_message",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "latency_ms",
        "created_at",
        "started_at",
        "finished_at",
    }
    assert {fk.target_fullname for fk in ai_runs.c.digest_id.foreign_keys} == {
        "daily_digests.id"
    }
    assert any(index.name == "ai_runs_digest_created_idx" for index in ai_runs.indexes)


def test_sync_jobs_accepts_digest_jobs_with_real_digest_foreign_key() -> None:
    sync_jobs = Base.metadata.tables["sync_jobs"]

    assert "digest_id" in sync_jobs.c
    assert {fk.target_fullname for fk in sync_jobs.c.digest_id.foreign_keys} == {
        "daily_digests.id"
    }
    job_type_checks = [
        str(constraint.sqltext)
        for constraint in sync_jobs.constraints
        if constraint.name == "sync_jobs_job_type_check"
    ]
    assert job_type_checks == [
        "job_type IN ("
        "'sync_today_emails', "
        "'generate_daily_digest', "
        "'refresh_daily_digest', "
        "'check_new_emails_after_digest', "
        "'refresh_access_token'"
        ")"
    ]
