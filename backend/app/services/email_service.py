from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.user import User
from app.providers.base import ProviderError
from app.providers.gmail import GmailProvider
from app.services.credential_encryption_service import CredentialEncryptionService


class EmailServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _not_found() -> EmailServiceError:
    return EmailServiceError("INVALID_REQUEST", "Email not found.", 404)


def _today_window(timezone: str, now: datetime | None = None) -> tuple[datetime, datetime]:
    resolved_now = now or datetime.now(UTC)
    if resolved_now.tzinfo is None:
        resolved_now = resolved_now.replace(tzinfo=UTC)
    try:
        user_zone = ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        user_zone = ZoneInfo(get_settings().default_timezone)
    local_now = resolved_now.astimezone(user_zone)
    local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_start.astimezone(UTC), resolved_now.astimezone(UTC)


def list_today_emails(
    db: Session,
    *,
    user: User,
    is_read: bool | None = None,
    sort: str = "received_at_desc",
    source: str = "all",
    priority: str | None = None,
    now: datetime | None = None,
) -> list[Email]:
    if sort != "received_at_desc":
        raise EmailServiceError("INVALID_REQUEST", "Unsupported email sort.")
    if source != "all" or priority is not None:
        raise EmailServiceError(
            "INVALID_REQUEST",
            "Priority-backed email filtering is not available in this phase.",
        )

    window_start, window_end = _today_window(user.timezone, now)
    statement = (
        select(Email)
        .join(Mailbox, Email.mailbox_id == Mailbox.id)
        .where(
            Email.user_id == user.id,
            Mailbox.status == "active",
            Email.received_at >= window_start,
            Email.received_at <= window_end,
        )
        .order_by(Email.received_at.desc())
    )
    if is_read is not None:
        statement = statement.where(Email.is_read == is_read)
    return list(db.scalars(statement).all())


def get_owned_email(db: Session, *, user: User, email_id: UUID) -> Email:
    email = db.scalar(select(Email).where(Email.id == email_id, Email.user_id == user.id))
    if email is None:
        raise _not_found()
    return email


def mark_email_read_state(
    db: Session,
    *,
    user: User,
    email_id: UUID,
    read: bool,
    provider: object | None = None,
    now: datetime | None = None,
) -> Email:
    email = get_owned_email(db, user=user, email_id=email_id)
    mailbox = db.get(Mailbox, email.mailbox_id)
    if mailbox is None or mailbox.user_id != user.id:
        raise _not_found()
    if mailbox.provider != "gmail":
        raise EmailServiceError("INVALID_REQUEST", "Unsupported email provider.")
    if mailbox.permission_mode != "write_enabled":
        raise EmailServiceError("FORBIDDEN", "Mailbox is read-only.", 403)
    if "https://www.googleapis.com/auth/gmail.modify" not in (mailbox.granted_scopes or []):
        raise EmailServiceError("FORBIDDEN", "Mailbox does not have Gmail modify scope.", 403)

    refresh_token = _decrypt_refresh_token(db, mailbox_id=mailbox.id)
    gmail_provider = provider or GmailProvider()
    try:
        access_token = gmail_provider.refresh_access_token(refresh_token)
        labels = (
            gmail_provider.mark_as_read(access_token, email.external_id)
            if read
            else gmail_provider.mark_as_unread(access_token, email.external_id)
        )
    except ProviderError as exc:
        raise EmailServiceError(exc.code, exc.message, exc.status_code) from exc

    email.is_read = read
    email.provider_labels = labels or _local_labels_after_read_state(
        email.provider_labels, read=read
    )
    resolved_now = now or datetime.now(UTC)
    email.last_synced_at = resolved_now
    email.updated_at = resolved_now
    db.flush()
    return email


def _decrypt_refresh_token(db: Session, *, mailbox_id: UUID) -> str:
    credential = db.get(MailboxCredential, mailbox_id)
    if credential is None or not credential.refresh_token_encrypted:
        raise EmailServiceError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is required.",
            401,
        )

    try:
        return CredentialEncryptionService().decrypt(credential.refresh_token_encrypted)
    except Exception as exc:
        raise EmailServiceError(
            "MAILBOX_REAUTH_REQUIRED",
            "Gmail authorization is required.",
            401,
        ) from exc


def _local_labels_after_read_state(labels: list[str], *, read: bool) -> list[str]:
    without_unread = [label for label in labels if label != "UNREAD"]
    if read:
        return without_unread
    return without_unread + ["UNREAD"]
