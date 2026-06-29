from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_archive_state import MailboxArchiveState
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.providers.base import ProviderArchiveBatch, ProviderEmailMessage
from app.services.auth_service import register_user
from app.services.credential_encryption_service import CredentialEncryptionService
from app.services.email_archive_service import (
    enqueue_archive_backfill_job,
    execute_queued_archive_job,
)


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _create_mailbox(*, provider: str = "gmail") -> tuple[UUID, UUID]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email("archive-user"),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider=provider,
            provider_account_id=f"{provider}-{uuid4().hex}",
            email_address=_email(f"archive-{provider}"),
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
                credential_type="oauth2" if provider == "gmail" else "imap_password",
                refresh_token_encrypted=CredentialEncryptionService().encrypt(
                    "fake-refresh-token"
                )
                if provider == "gmail"
                else None,
                imap_password_encrypted=CredentialEncryptionService().encrypt(
                    "fake-imap-password"
                )
                if provider == "imap"
                else None,
                scopes_snapshot=mailbox.granted_scopes,
                credentials_json={
                    "host": "imap.example.com",
                    "port": 993,
                    "username": "imap@example.com",
                    "folder": "INBOX",
                    "use_ssl": True,
                }
                if provider == "imap"
                else {},
            )
        )
        db.commit()
        return user.id, mailbox.id


def _create_additional_mailbox(user_id: UUID, *, provider: str = "gmail") -> UUID:
    with SessionLocal() as db:
        mailbox = Mailbox(
            user_id=user_id,
            provider=provider,
            provider_account_id=f"{provider}-{uuid4().hex}",
            email_address=_email(f"archive-extra-{provider}"),
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
                credential_type="oauth2" if provider == "gmail" else "imap_password",
                refresh_token_encrypted=CredentialEncryptionService().encrypt(
                    "fake-refresh-token"
                )
                if provider == "gmail"
                else None,
                imap_password_encrypted=CredentialEncryptionService().encrypt(
                    "fake-imap-password"
                )
                if provider == "imap"
                else None,
                scopes_snapshot=mailbox.granted_scopes,
                credentials_json={},
            )
        )
        db.commit()
        return mailbox.id


def _message(external_id: str, *, received_at: datetime) -> ProviderEmailMessage:
    return ProviderEmailMessage(
        external_id=external_id,
        external_thread_id=f"thread-{external_id}",
        internet_message_id=f"<{external_id}@example.com>",
        subject=f"Subject {external_id}",
        from_name="Sender",
        from_address="sender@example.com",
        to_addresses=["me@example.com"],
        cc_addresses=[],
        snippet=f"Snippet {external_id}",
        body_text="body should not be archived by default",
        body_text_truncated=False,
        received_at=received_at,
        is_read=False,
        provider_labels=["INBOX", "UNREAD"],
        gmail_history_id="history-1",
        raw_payload_hash="a" * 64,
    )


class FakeArchiveProvider:
    def __init__(self, batches: list[ProviderArchiveBatch]) -> None:
        self.batches = batches
        self.cursors: list[dict[str, object] | None] = []

    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token in {"fake-refresh-token", "fake-imap-password"}
        return refresh_token

    def list_archive_batch(
        self,
        access_token: str,
        *,
        cursor: dict[str, object] | None,
        batch_size: int,
    ) -> ProviderArchiveBatch:
        self.cursors.append(cursor)
        assert batch_size == 2
        return self.batches.pop(0)


class DummyLock:
    def release(self) -> None:
        return None


def test_enqueue_archive_backfill_job_creates_state_and_queued_job(monkeypatch) -> None:
    user_id, mailbox_id = _create_mailbox()
    dispatched: list[UUID] = []

    monkeypatch.setattr(
        "app.services.email_archive_service.dispatch_archive_backfill_job",
        lambda job_id: dispatched.append(job_id) or f"celery-archive-{job_id}",
    )

    with SessionLocal() as db:
        result = enqueue_archive_backfill_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            batch_size=2,
        )
        db.commit()

    assert result.status == "queued"
    assert dispatched == [result.job_id]
    with SessionLocal() as db:
        state = db.scalar(
            select(MailboxArchiveState).where(
                MailboxArchiveState.mailbox_id == mailbox_id
            )
        )
        job = db.get(SyncJob, result.job_id)
        assert state is not None
        assert state.status == "not_started"
        assert state.total_synced_count == 0
        assert job is not None
        assert job.job_type == "email_archive_backfill"
        assert job.status == "queued"
        assert job.payload_json["sync_mode"] == "full_history"


def test_duplicate_archive_job_same_mailbox_is_reused_but_other_mailbox_is_allowed(
    monkeypatch,
) -> None:
    user_id, first_mailbox_id = _create_mailbox()
    second_mailbox_id = _create_additional_mailbox(user_id)
    dispatched: list[UUID] = []
    monkeypatch.setattr(
        "app.services.email_archive_service.dispatch_archive_backfill_job",
        lambda job_id: dispatched.append(job_id) or f"celery-archive-{job_id}",
    )

    with SessionLocal() as db:
        first = enqueue_archive_backfill_job(
            db, user_id=user_id, mailbox_id=first_mailbox_id
        )
        duplicate = enqueue_archive_backfill_job(
            db, user_id=user_id, mailbox_id=first_mailbox_id
        )
        other = enqueue_archive_backfill_job(
            db, user_id=user_id, mailbox_id=second_mailbox_id
        )
        db.commit()

    assert duplicate.job_id == first.job_id
    assert other.job_id != first.job_id
    assert dispatched == [first.job_id, other.job_id]


def test_execute_archive_job_upserts_metadata_only_and_updates_progress(
    monkeypatch,
) -> None:
    user_id, mailbox_id = _create_mailbox()
    now = datetime(2026, 6, 29, 9, 0, tzinfo=UTC)
    provider = FakeArchiveProvider(
        [
            ProviderArchiveBatch(
                messages=[
                    _message("archive-new", received_at=now),
                    _message("archive-old", received_at=now - timedelta(days=3)),
                ],
                cursor={"page_token": "next-page"},
                is_complete=False,
            ),
            ProviderArchiveBatch(messages=[], cursor=None, is_complete=True),
        ]
    )
    monkeypatch.setattr(
        "app.services.email_archive_service.acquire_archive_lock",
        lambda *, mailbox_id, job_id: DummyLock(),
    )

    with SessionLocal() as db:
        queued = enqueue_archive_backfill_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            dispatch=False,
            batch_size=2,
            max_batches=2,
            now=now,
        )
        job = db.get(SyncJob, queued.job_id)
        assert job is not None
        job.status = "queued"
        job.celery_task_id = f"manual-{job.id}"
        result = execute_queued_archive_job(
            db,
            job_id=queued.job_id,
            provider=provider,
            now=now,
        )
        db.commit()

    assert result.status == "completed"
    assert result.synced_count == 2
    assert provider.cursors == [None, {"page_token": "next-page"}]
    with SessionLocal() as db:
        state = db.scalar(
            select(MailboxArchiveState).where(
                MailboxArchiveState.mailbox_id == mailbox_id
            )
        )
        emails = db.scalars(
            select(Email)
            .where(Email.mailbox_id == mailbox_id)
            .order_by(Email.received_at.desc())
        ).all()
        assert state is not None
        assert state.status == "complete"
        assert state.total_synced_count == 2
        assert state.batch_count == 2
        assert state.newest_synced_at == now
        assert state.oldest_synced_at == now - timedelta(days=3)
        assert [email.external_id for email in emails] == ["archive-new", "archive-old"]
        assert all(email.body_text is None for email in emails)
        assert all(email.body_cache_status == "not_cached" for email in emails)
