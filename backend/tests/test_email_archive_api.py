from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_archive_state import MailboxArchiveState
from app.db.models.mailbox_credential import MailboxCredential
from app.db.session import SessionLocal
from app.main import app
from app.services.credential_encryption_service import CredentialEncryptionService


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _register_client(prefix: str) -> tuple[TestClient, UUID]:
    client = TestClient(app)
    response = client.post(
        "/api/auth/register",
        json={"email": _email(prefix), "password": "strong-password"},
    )
    assert response.status_code == 201
    return client, UUID(response.json()["data"]["user"]["id"])


def _create_mailbox(user_id: UUID, *, provider: str = "gmail") -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider=provider,
            provider_account_id=f"archive-api-{uuid4().hex}",
            email_address=_email("archive-api-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"]
            if provider == "gmail"
            else [],
            status="active",
        )
        db.add(mailbox)
        db.flush()
        db.add(
            MailboxCredential(
                mailbox_id=mailbox.id,
                credential_type="oauth2",
                refresh_token_encrypted=CredentialEncryptionService().encrypt(
                    "fake-refresh-token"
                ),
                scopes_snapshot=mailbox.granted_scopes,
                credentials_json={},
            )
        )
        db.commit()
        return mailbox.id


def _create_archived_email(
    user_id: UUID,
    mailbox_id: UUID,
    *,
    external_id: str,
    received_at: datetime,
    subject: str,
    is_read: bool = False,
) -> UUID:
    with SessionLocal() as db:
        email = Email(
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider="gmail",
            external_id=external_id,
            external_thread_id=f"thread-{external_id}",
            subject=subject,
            from_name="Alice",
            from_address="alice@example.com",
            to_addresses=["me@example.com"],
            cc_addresses=[],
            snippet=f"Snippet {subject}",
            body_text=None,
            body_text_truncated=False,
            body_cache_status="not_cached",
            received_at=received_at,
            sent_at=received_at,
            is_read=is_read,
            is_starred=False,
            has_attachments=True,
            provider_labels=["INBOX"] if is_read else ["INBOX", "UNREAD"],
            provider_metadata_json={},
        )
        db.add(email)
        db.commit()
        return email.id


def test_archive_job_api_creates_archive_job_and_state(monkeypatch) -> None:
    client, user_id = _register_client("archive-api-job")
    mailbox_id = _create_mailbox(user_id)
    dispatched: list[UUID] = []

    monkeypatch.setattr(
        "app.services.email_archive_service.dispatch_archive_backfill_job",
        lambda job_id: dispatched.append(job_id) or f"celery-archive-{job_id}",
    )

    response = client.post(f"/api/mailboxes/{mailbox_id}/archive-jobs")

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["job"]["job_type"] == "email_archive_backfill"
    assert body["job"]["status"] == "queued"
    assert body["job"]["mailbox_id"] == str(mailbox_id)
    assert body["archive_state"]["status"] == "not_started"
    assert dispatched == [UUID(body["job"]["job_id"])]


def test_email_query_range_filters_are_local_database_filters(monkeypatch) -> None:
    client, user_id = _register_client("archive-api-range")
    mailbox_id = _create_mailbox(user_id)
    now = datetime.now(UTC)
    today_id = _create_archived_email(
        user_id,
        mailbox_id,
        external_id="range-today",
        received_at=now - timedelta(hours=1),
        subject="Today planning",
    )
    week_id = _create_archived_email(
        user_id,
        mailbox_id,
        external_id="range-week",
        received_at=now - timedelta(days=6),
        subject="Weekly review",
        is_read=True,
    )
    _create_archived_email(
        user_id,
        mailbox_id,
        external_id="range-old",
        received_at=now - timedelta(days=40),
        subject="Old note",
    )

    def fail_if_provider_is_used(*args, **kwargs):
        raise AssertionError("Emails query must not call Gmail or IMAP providers")

    monkeypatch.setattr("app.services.email_service.GmailProvider", fail_if_provider_is_used)

    today = client.get("/api/emails", params={"range": "today"})
    last_7 = client.get("/api/emails", params={"range": "last_7_days"})
    unread_week = client.get(
        "/api/emails",
        params={"range": "last_7_days", "is_read": "false", "q": "planning"},
    )
    all_synced = client.get("/api/emails", params={"range": "all_synced", "limit": 10})

    assert today.status_code == 200
    assert [email["id"] for email in today.json()["data"]["emails"]] == [str(today_id)]
    assert last_7.status_code == 200
    assert [email["id"] for email in last_7.json()["data"]["emails"]] == [
        str(today_id),
        str(week_id),
    ]
    assert unread_week.status_code == 200
    assert [email["id"] for email in unread_week.json()["data"]["emails"]] == [
        str(today_id)
    ]
    assert all_synced.json()["data"]["pagination"]["total"] == 3
    assert all_synced.json()["data"]["range"] == "all_synced"


def test_custom_range_and_email_detail_return_archive_metadata() -> None:
    client, user_id = _register_client("archive-api-detail")
    mailbox_id = _create_mailbox(user_id)
    with SessionLocal() as db:
        db.add(
            MailboxArchiveState(
                mailbox_id=mailbox_id,
                provider="gmail",
                status="running",
                total_synced_count=42,
                batch_count=3,
                cursor={"page_token": "next"},
            )
        )
        db.commit()
    email_id = _create_archived_email(
        user_id,
        mailbox_id,
        external_id="custom-detail",
        received_at=datetime(2026, 6, 15, 8, 0, tzinfo=UTC),
        subject="Custom detail",
    )

    listing = client.get(
        "/api/emails",
        params={"range": "custom", "from": "2026-06-01", "to": "2026-06-30"},
    )
    detail = client.get(f"/api/emails/{email_id}")

    assert listing.status_code == 200
    data = listing.json()["data"]
    assert data["archive_state"]["status"] == "running"
    assert data["archive_state"]["total_synced_count"] == 42
    assert data["emails"][0]["mailbox_email"] is not None
    assert data["emails"][0]["has_attachments"] is True
    assert detail.status_code == 200
    email = detail.json()["data"]["email"]
    assert email["id"] == str(email_id)
    assert email["body_cache_status"] == "not_cached"
    assert email["body_text"] is None

