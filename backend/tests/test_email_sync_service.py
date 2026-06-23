from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import select

from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.sync_job import SyncJob
from app.db.session import SessionLocal
from app.providers.base import ProviderEmailMessage, ProviderError
from app.providers.imap import ImapMailboxConfig
from app.services.auth_service import register_user
from app.services.credential_encryption_service import CredentialEncryptionService
from app.services.email_sync_service import (
    EmailSyncError,
    enqueue_sync_today_job,
    execute_queued_sync_job,
    sync_today_emails,
)


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex}@example.com"


def _create_connected_mailbox() -> tuple[UUID, UUID]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email("sync-user"),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=f"provider-{uuid4().hex}",
            email_address=_email("mailbox"),
            permission_mode="write_enabled",
            granted_scopes=["https://www.googleapis.com/auth/gmail.modify"],
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
        return user.id, mailbox.id


def _create_connected_imap_mailbox() -> tuple[UUID, UUID]:
    with SessionLocal() as db:
        user = register_user(
            db,
            email=_email("sync-imap-user"),
            password="strong-password",
            timezone="Asia/Shanghai",
        )
        mailbox = Mailbox(
            user_id=user.id,
            provider="imap",
            provider_account_id=f"imap-{uuid4().hex}",
            email_address=_email("imap-mailbox"),
            permission_mode="write_enabled",
            granted_scopes=[],
            status="active",
        )
        db.add(mailbox)
        db.flush()
        db.add(
            MailboxCredential(
                mailbox_id=mailbox.id,
                credential_type="imap_password",
                imap_password_encrypted=CredentialEncryptionService().encrypt(
                    "fake-imap-password"
                ),
                scopes_snapshot=[],
                credentials_json={
                    "host": "imap.example.com",
                    "port": 993,
                    "username": "imap-user@example.com",
                    "folder": "INBOX",
                    "use_ssl": True,
                },
            )
        )
        db.commit()
        return user.id, mailbox.id


def _message(
    external_id: str,
    *,
    subject: str,
    unread: bool,
    received_at: datetime,
) -> ProviderEmailMessage:
    labels = ["INBOX", "UNREAD"] if unread else ["INBOX"]
    return ProviderEmailMessage(
        external_id=external_id,
        external_thread_id="thread-1",
        internet_message_id="<message@example.com>",
        subject=subject,
        from_name=None,
        from_address="sender@example.com",
        to_addresses=["me@example.com"],
        cc_addresses=[],
        snippet="preview",
        body_text="body",
        body_text_truncated=False,
        received_at=received_at,
        is_read=not unread,
        provider_labels=labels,
        gmail_history_id="history-1",
        raw_payload_hash="a" * 64,
    )


class FakeProvider:
    def __init__(self, messages: list[ProviderEmailMessage]) -> None:
        self.messages = messages
        self.window_start: datetime | None = None
        self.window_end: datetime | None = None

    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-refresh-token"
        return "fake-access-token"

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        assert access_token == "fake-access-token"
        self.window_start = window_start
        self.window_end = window_end
        return self.messages


class FakeImapProvider:
    def __init__(self, messages: list[ProviderEmailMessage]) -> None:
        self.messages = messages
        self.config: ImapMailboxConfig | None = None
        self.window_start: datetime | None = None
        self.window_end: datetime | None = None

    def with_mailbox_config(self, config: ImapMailboxConfig) -> "FakeImapProvider":
        self.config = config
        return self

    def refresh_access_token(self, refresh_token: str) -> str:
        assert refresh_token == "fake-imap-password"
        return refresh_token

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        assert access_token == "fake-imap-password"
        self.window_start = window_start
        self.window_end = window_end
        return self.messages


class FailingProvider:
    def refresh_access_token(self, refresh_token: str) -> str:
        return "fake-access-token"

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        raise ProviderError("PROVIDER_SYNC_FAILED", "Gmail request failed.", 502)


class ReauthProvider:
    def refresh_access_token(self, refresh_token: str) -> str:
        raise ProviderError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is no longer valid.",
            401,
        )


def test_sync_today_emails_upserts_emails_and_creates_sync_job() -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    provider = FakeProvider(
        [
            _message(
                "gmail-message-1",
                subject="Initial subject",
                unread=True,
                received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
            )
        ]
    )
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    with SessionLocal() as db:
        result = sync_today_emails(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider=provider,
            now=now,
        )
        db.commit()

    assert result.synced_count == 1
    assert provider.window_start == datetime(2026, 6, 18, 16, 0, tzinfo=UTC)
    assert provider.window_end == now

    with SessionLocal() as db:
        email = db.scalar(
            select(Email).where(
                Email.mailbox_id == mailbox_id,
                Email.external_id == "gmail-message-1",
            )
        )
        job = db.scalar(
            select(SyncJob)
            .where(SyncJob.mailbox_id == mailbox_id)
            .order_by(SyncJob.created_at.desc())
        )
        mailbox = db.get(Mailbox, mailbox_id)

        assert email is not None
        assert email.user_id == user_id
        assert email.subject == "Initial subject"
        assert email.is_read is False
        assert email.provider_labels == ["INBOX", "UNREAD"]
        assert job is not None
        assert job.status == "succeeded"
        assert job.job_type == "sync_today_emails"
        assert job.error_message is None
        assert mailbox is not None
        assert mailbox.last_successful_sync_at == now

    provider.messages = [
        _message(
            "gmail-message-1",
            subject="Updated subject",
            unread=False,
            received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
        )
    ]
    with SessionLocal() as db:
        result = sync_today_emails(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider=provider,
            now=now,
        )
        db.commit()

    assert result.synced_count == 1
    with SessionLocal() as db:
        emails = db.scalars(
            select(Email).where(
                Email.mailbox_id == mailbox_id,
                Email.external_id == "gmail-message-1",
            )
        ).all()
        assert len(emails) == 1
        assert emails[0].subject == "Updated subject"
        assert emails[0].is_read is True


def test_sync_today_emails_records_failed_sync_job() -> None:
    user_id, mailbox_id = _create_connected_mailbox()

    with SessionLocal() as db:
        try:
            sync_today_emails(
                db,
                user_id=user_id,
                mailbox_id=mailbox_id,
                provider=FailingProvider(),
                now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            )
        except EmailSyncError as exc:
            assert exc.code == "PROVIDER_SYNC_FAILED"
            db.commit()
        else:
            raise AssertionError("sync failure should raise EmailSyncError")

    with SessionLocal() as db:
        job = db.scalar(
            select(SyncJob)
            .where(SyncJob.mailbox_id == mailbox_id)
            .order_by(SyncJob.created_at.desc())
        )
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == "PROVIDER_SYNC_FAILED"
        assert job.error_message == "Gmail request failed."
        mailbox = db.get(Mailbox, mailbox_id)
        assert mailbox is not None
        assert mailbox.status == "active"


def test_sync_today_emails_marks_mailbox_reauth_only_for_reauth_errors() -> None:
    user_id, mailbox_id = _create_connected_mailbox()

    with SessionLocal() as db:
        try:
            sync_today_emails(
                db,
                user_id=user_id,
                mailbox_id=mailbox_id,
                provider=ReauthProvider(),
                now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            )
        except EmailSyncError as exc:
            assert exc.code == "MAILBOX_REAUTH_REQUIRED"
            db.commit()
        else:
            raise AssertionError("reauth failure should raise EmailSyncError")

    with SessionLocal() as db:
        mailbox = db.get(Mailbox, mailbox_id)
        job = db.scalar(
            select(SyncJob)
            .where(SyncJob.mailbox_id == mailbox_id)
            .order_by(SyncJob.created_at.desc())
        )
        assert mailbox is not None
        assert mailbox.status == "reauth_required"
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == "MAILBOX_REAUTH_REQUIRED"


def test_enqueue_sync_today_job_creates_queued_job_and_dispatches(monkeypatch) -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-job-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    with SessionLocal() as db:
        result = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()
        job_id = result.job_id

    assert dispatched == [job_id]
    assert result.status == "queued"
    with SessionLocal() as db:
        job = db.get(SyncJob, job_id)
        assert job is not None
        assert job.user_id == user_id
        assert job.mailbox_id == mailbox_id
        assert job.status == "queued"
        assert job.celery_task_id == f"celery-job-{job_id}"


def test_enqueue_sync_today_job_reuses_existing_queued_job(monkeypatch) -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    with SessionLocal() as db:
        first = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        second = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=datetime(2026, 6, 19, 10, 1, tzinfo=UTC),
        )
        db.commit()

    assert second.job_id == first.job_id
    assert second.status == "queued"
    assert dispatched == [first.job_id]

    with SessionLocal() as db:
        jobs = db.scalars(
            select(SyncJob).where(
                SyncJob.user_id == user_id,
                SyncJob.mailbox_id == mailbox_id,
                SyncJob.job_type == "sync_today_emails",
            )
        ).all()
        assert len(jobs) == 1


def test_enqueue_sync_today_job_reuses_existing_running_job(monkeypatch) -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    dispatched: list[UUID] = []

    def fake_dispatch(job_id: UUID) -> str:
        dispatched.append(job_id)
        return f"celery-running-{job_id}"

    monkeypatch.setattr(
        "app.services.email_sync_service.dispatch_email_sync_job",
        fake_dispatch,
    )

    with SessionLocal() as db:
        first = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        job = db.get(SyncJob, first.job_id)
        assert job is not None
        job.status = "running"
        second = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=datetime(2026, 6, 19, 10, 1, tzinfo=UTC),
        )
        db.commit()

    assert second.job_id == first.job_id
    assert second.status == "running"
    assert dispatched == [first.job_id]


def test_execute_queued_sync_job_updates_same_job_and_mailbox() -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)
    provider = FakeProvider(
        [
            _message(
                "queued-gmail-message",
                subject="Queued subject",
                unread=True,
                received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
            )
        ]
    )

    with SessionLocal() as db:
        result = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            dispatch=False,
            now=now,
        )
        job_id = result.job_id
        executed = execute_queued_sync_job(
            db,
            job_id=job_id,
            provider=provider,
            now=now,
        )
        db.commit()

    assert executed.job_id == job_id
    assert executed.status == "completed"
    assert executed.synced_count == 1
    with SessionLocal() as db:
        job = db.get(SyncJob, job_id)
        mailbox = db.get(Mailbox, mailbox_id)
        email = db.scalar(select(Email).where(Email.external_id == "queued-gmail-message"))
        assert job is not None
        assert job.status == "succeeded"
        assert job.payload_json == {"synced_count": 1}
        assert mailbox is not None
        assert mailbox.last_successful_sync_at == now
        assert email is not None
        assert email.subject == "Queued subject"


def test_execute_queued_sync_job_marks_duplicate_when_mailbox_lock_is_held(
    monkeypatch,
) -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    now = datetime(2026, 6, 19, 10, 0, tzinfo=UTC)

    monkeypatch.setattr(
        "app.services.email_sync_service.acquire_mailbox_sync_lock",
        lambda *args, **kwargs: None,
    )

    with SessionLocal() as db:
        result = enqueue_sync_today_job(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            dispatch=False,
            now=now,
        )
        try:
            execute_queued_sync_job(
                db,
                job_id=result.job_id,
                provider=FakeProvider([]),
                now=now,
            )
        except EmailSyncError as exc:
            assert exc.code == "worker_lock_conflict"
            db.commit()
        else:
            raise AssertionError("lock conflict should fail the duplicate worker job")

    with SessionLocal() as db:
        job = db.get(SyncJob, result.job_id)
        assert job is not None
        assert job.status == "failed"
        assert job.error_code == "worker_lock_conflict"


def test_sync_today_emails_resolves_provider_from_registry(monkeypatch) -> None:
    user_id, mailbox_id = _create_connected_mailbox()
    provider = FakeProvider(
        [
            _message(
                "registry-gmail-message",
                subject="Registry subject",
                unread=True,
                received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
            )
        ]
    )
    calls: list[str] = []

    def fake_get_mailbox_provider(provider_key: str):
        calls.append(provider_key)
        return provider

    monkeypatch.setattr(
        "app.services.email_sync_service.get_mailbox_provider",
        fake_get_mailbox_provider,
    )

    with SessionLocal() as db:
        result = sync_today_emails(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()

    assert result.synced_count == 1
    assert calls == ["gmail", "gmail"]

    with SessionLocal() as db:
        email = db.scalar(select(Email).where(Email.external_id == "registry-gmail-message"))
        assert email is not None
        assert email.subject == "Registry subject"


def test_sync_today_emails_uses_imap_password_and_config() -> None:
    user_id, mailbox_id = _create_connected_imap_mailbox()
    external_id = f"INBOX:999:{uuid4().hex}"
    provider = FakeImapProvider(
        [
            _message(
                external_id,
                subject="IMAP sync subject",
                unread=False,
                received_at=datetime(2026, 6, 19, 2, 0, tzinfo=UTC),
            )
        ]
    )

    with SessionLocal() as db:
        result = sync_today_emails(
            db,
            user_id=user_id,
            mailbox_id=mailbox_id,
            provider=provider,
            now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )
        db.commit()

    assert result.synced_count == 1
    assert provider.config is not None
    assert provider.config.host == "imap.example.com"
    assert provider.config.username == "imap-user@example.com"
    assert provider.config.folder == "INBOX"

    with SessionLocal() as db:
        email = db.scalar(select(Email).where(Email.external_id == external_id))
        assert email is not None
        assert email.mailbox_id == mailbox_id
        assert email.provider == "imap"
        assert email.subject == "IMAP sync subject"
        assert email.gmail_history_id == "history-1"


def test_sync_today_emails_requires_imap_password() -> None:
    user_id, mailbox_id = _create_connected_imap_mailbox()
    provider = FakeImapProvider([])
    with SessionLocal() as db:
        credential = db.get(MailboxCredential, mailbox_id)
        assert credential is not None
        credential.imap_password_encrypted = None
        db.commit()

    with SessionLocal() as db:
        try:
            sync_today_emails(
                db,
                user_id=user_id,
                mailbox_id=mailbox_id,
                provider=provider,
                now=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
            )
        except EmailSyncError as exc:
            assert exc.code == "MAILBOX_REAUTH_REQUIRED"
            db.commit()
        else:
            raise AssertionError("IMAP sync should require stored password")
