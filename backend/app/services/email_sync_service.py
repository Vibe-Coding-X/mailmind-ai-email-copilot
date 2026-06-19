from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.sync_job import SyncJob
from app.db.models.user import User
from app.providers.base import ProviderEmailMessage, ProviderError
from app.providers.gmail import GmailProvider
from app.services.credential_encryption_service import CredentialEncryptionService


class EmailSyncError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class SyncTodayResult:
    mailbox_id: UUID
    status: str
    synced_count: int
    job_id: UUID


def sync_today_emails(
    db: Session,
    *,
    user_id: UUID | str,
    mailbox_id: UUID | str,
    provider: object | None = None,
    now: datetime | None = None,
) -> SyncTodayResult:
    resolved_user_id = _as_uuid(user_id)
    resolved_mailbox_id = _as_uuid(mailbox_id)
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    user = db.get(User, resolved_user_id)
    mailbox = db.scalar(
        select(Mailbox).where(
            Mailbox.id == resolved_mailbox_id,
            Mailbox.user_id == resolved_user_id,
        )
    )
    if user is None or mailbox is None:
        raise EmailSyncError("INVALID_REQUEST", "Mailbox not found.", 404)
    if mailbox.provider != "gmail":
        raise EmailSyncError("INVALID_REQUEST", "Unsupported mailbox provider.")
    if mailbox.status != "active":
        raise EmailSyncError(
            "MAILBOX_REAUTH_REQUIRED",
            "Mailbox is not connected.",
            401,
        )

    window_start, window_end = calculate_today_window(user.timezone, now=resolved_now)
    target_date = window_start.astimezone(_user_zone(user.timezone)).date()
    job = SyncJob(
        user_id=user.id,
        mailbox_id=mailbox.id,
        job_type="sync_today_emails",
        trigger_source="manual",
        job_key=f"sync_today_emails:{mailbox.id}:{target_date.isoformat()}",
        target_date=target_date,
        status="running",
        started_at=resolved_now,
        payload_json={},
    )
    db.add(job)
    mailbox.last_sync_at = resolved_now
    db.flush()

    try:
        refresh_token = _decrypt_refresh_token(db, mailbox_id=mailbox.id)
        gmail_provider = provider or GmailProvider()
        access_token = gmail_provider.refresh_access_token(refresh_token)
        messages = gmail_provider.list_messages_for_window(
            access_token,
            window_start=window_start,
            window_end=window_end,
        )
        synced_count = upsert_email_messages(
            db,
            mailbox=mailbox,
            messages=messages,
            window_start=window_start,
            window_end=window_end,
            synced_at=resolved_now,
        )
    except ProviderError as exc:
        if exc.code == "MAILBOX_REAUTH_REQUIRED":
            mailbox.status = "reauth_required"
        _fail_job(db, job=job, code=exc.code, message=exc.message, now=resolved_now)
        raise EmailSyncError(exc.code, exc.message, exc.status_code) from exc
    except EmailSyncError as exc:
        _fail_job(db, job=job, code=exc.code, message=exc.message, now=resolved_now)
        raise
    except Exception as exc:
        _fail_job(
            db,
            job=job,
            code="PROVIDER_SYNC_FAILED",
            message="Email sync failed.",
            now=resolved_now,
        )
        raise EmailSyncError("PROVIDER_SYNC_FAILED", "Email sync failed.", 502) from exc

    mailbox.last_successful_sync_at = resolved_now
    job.status = "succeeded"
    job.finished_at = resolved_now
    job.payload_json = {"synced_count": synced_count}
    db.flush()
    return SyncTodayResult(
        mailbox_id=mailbox.id,
        status="completed",
        synced_count=synced_count,
        job_id=job.id,
    )


def calculate_today_window(timezone: str, *, now: datetime) -> tuple[datetime, datetime]:
    user_zone = _user_zone(timezone)
    resolved_now = _ensure_utc(now)
    local_now = resolved_now.astimezone(user_zone)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_start.astimezone(UTC), resolved_now


def upsert_email_messages(
    db: Session,
    *,
    mailbox: Mailbox,
    messages: list[ProviderEmailMessage],
    window_start: datetime,
    window_end: datetime,
    synced_at: datetime,
) -> int:
    synced_count = 0
    for message in messages:
        if not message.external_id:
            continue
        if not window_start <= message.received_at <= window_end:
            continue

        email = db.scalar(
            select(Email).where(
                Email.mailbox_id == mailbox.id,
                Email.external_id == message.external_id,
            )
        )
        if email is None:
            email = Email(
                user_id=mailbox.user_id,
                mailbox_id=mailbox.id,
                provider=mailbox.provider,
                external_id=message.external_id,
                first_synced_at=synced_at,
                created_at=synced_at,
            )
            db.add(email)

        email.external_thread_id = message.external_thread_id
        email.internet_message_id = message.internet_message_id
        email.subject = message.subject
        email.from_name = message.from_name
        email.from_address = message.from_address
        email.to_addresses = message.to_addresses
        email.cc_addresses = message.cc_addresses
        email.snippet = message.snippet
        email.body_text = message.body_text
        email.body_text_truncated = message.body_text_truncated
        email.received_at = message.received_at
        email.is_read = message.is_read
        email.provider_labels = message.provider_labels
        email.gmail_history_id = message.gmail_history_id
        email.last_synced_at = synced_at
        email.updated_at = synced_at
        synced_count += 1

    db.flush()
    return synced_count


def _decrypt_refresh_token(db: Session, *, mailbox_id: UUID) -> str:
    credential = db.get(MailboxCredential, mailbox_id)
    if credential is None or not credential.refresh_token_encrypted:
        raise EmailSyncError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is required.",
            401,
        )

    try:
        return CredentialEncryptionService().decrypt(credential.refresh_token_encrypted)
    except Exception as exc:
        raise EmailSyncError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is required.",
            401,
        ) from exc


def _fail_job(
    db: Session,
    *,
    job: SyncJob,
    code: str,
    message: str,
    now: datetime,
) -> None:
    job.status = "failed"
    job.error_code = code
    job.error_message = message[:1000]
    job.finished_at = now
    db.flush()


def _as_uuid(value: UUID | str) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _user_zone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo(get_settings().default_timezone)
