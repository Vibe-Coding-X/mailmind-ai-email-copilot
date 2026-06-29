from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_archive_state import MailboxArchiveState
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.user import User
from app.providers.base import ProviderError
from app.providers.gmail import GmailProvider
from app.providers.registry import (
    ProviderRegistryError,
    get_mailbox_provider as registry_get_mailbox_provider,
)
from app.services.credential_encryption_service import CredentialEncryptionService
from app.services.user_action_service import record_completed_action, record_failed_action


class EmailServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class EmailQueryResult:
    emails: list[Email]
    limit: int
    offset: int
    has_more: bool
    total: int
    range_type: str
    archive_state: dict[str, object]


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
        .order_by(Email.received_at.desc(), Email.id.desc())
    )
    if is_read is not None:
        statement = statement.where(Email.is_read == is_read)
    return list(db.scalars(statement).all())


def list_emails(
    db: Session,
    *,
    user: User,
    limit: int = 50,
    offset: int = 0,
    is_read: bool | None = None,
    mailbox_id: UUID | None = None,
    received_from: datetime | None = None,
    received_to: datetime | None = None,
    range_type: str = "all_synced",
    custom_from: date | None = None,
    custom_to: date | None = None,
    q: str | None = None,
    sort: str = "received_at_desc",
    now: datetime | None = None,
) -> EmailQueryResult:
    resolved_limit = max(1, min(limit, 100))
    resolved_offset = max(0, offset)
    if sort not in {"received_at_desc", "received_at_asc"}:
        raise EmailServiceError("INVALID_REQUEST", "Unsupported email sort.")

    filters = [Email.user_id == user.id, Mailbox.status == "active"]
    if mailbox_id is not None:
        _ensure_owned_active_mailbox(db, user=user, mailbox_id=mailbox_id)
        filters.append(Email.mailbox_id == mailbox_id)
    if is_read is not None:
        filters.append(Email.is_read == is_read)
    range_start, range_end, resolved_range_type = _email_range_window(
        user=user,
        range_type=range_type,
        custom_from=custom_from,
        custom_to=custom_to,
        now=now,
    )
    if received_from is not None:
        range_start = _ensure_utc(received_from)
    if received_to is not None:
        range_end = _ensure_utc(received_to)
    if range_start is not None:
        filters.append(Email.received_at >= range_start)
    if range_end is not None:
        filters.append(Email.received_at <= range_end)
    keyword = (q or "").strip()
    if keyword:
        pattern = f"%{keyword}%"
        filters.append(
            or_(
                Email.subject.ilike(pattern),
                Email.from_address.ilike(pattern),
                Email.snippet.ilike(pattern),
                Email.body_text.ilike(pattern),
            )
        )

    order_column = Email.received_at.asc() if sort == "received_at_asc" else Email.received_at.desc()
    base_statement = select(Email).join(Mailbox, Email.mailbox_id == Mailbox.id).where(*filters)
    total = int(
        db.scalar(
            select(func.count())
            .select_from(Email)
            .join(Mailbox, Email.mailbox_id == Mailbox.id)
            .where(*filters)
        )
        or 0
    )
    statement = base_statement.order_by(order_column, Email.id.desc()).offset(
        resolved_offset
    ).limit(resolved_limit + 1)
    rows = list(db.scalars(statement).unique().all())
    return EmailQueryResult(
        emails=rows[:resolved_limit],
        limit=resolved_limit,
        offset=resolved_offset,
        has_more=len(rows) > resolved_limit,
        total=total,
        range_type=resolved_range_type,
        archive_state=archive_state_summary(db, user=user, mailbox_id=mailbox_id),
    )


def get_owned_email(db: Session, *, user: User, email_id: UUID) -> Email:
    email = db.scalar(select(Email).where(Email.id == email_id, Email.user_id == user.id))
    if email is None:
        raise _not_found()
    return email


def get_mailbox_provider(provider_key: str) -> object:
    normalized = provider_key.strip().lower()
    if normalized == "gmail":
        return GmailProvider()
    return registry_get_mailbox_provider(normalized)


def _ensure_owned_active_mailbox(db: Session, *, user: User, mailbox_id: UUID) -> None:
    mailbox = db.scalar(
        select(Mailbox).where(
            Mailbox.id == mailbox_id,
            Mailbox.user_id == user.id,
            Mailbox.status == "active",
        )
    )
    if mailbox is None:
        raise EmailServiceError("INVALID_REQUEST", "Mailbox not found.", 404)


def archive_state_summary(
    db: Session, *, user: User, mailbox_id: UUID | None = None
) -> dict[str, object]:
    statement = (
        select(MailboxArchiveState)
        .join(Mailbox, MailboxArchiveState.mailbox_id == Mailbox.id)
        .where(Mailbox.user_id == user.id)
    )
    if mailbox_id is not None:
        statement = statement.where(MailboxArchiveState.mailbox_id == mailbox_id)
    states = list(db.scalars(statement).all())
    if not states:
        return {
            "status": "not_started",
            "is_complete": False,
            "total_synced_count": 0,
            "batch_count": 0,
            "newest_synced_at": None,
            "oldest_synced_at": None,
            "message": "Local archive has not started.",
        }
    if mailbox_id is not None and len(states) == 1:
        state = states[0]
        return {
            "status": state.status,
            "is_complete": state.status == "complete",
            "total_synced_count": state.total_synced_count,
            "batch_count": state.batch_count,
            "newest_synced_at": state.newest_synced_at,
            "oldest_synced_at": state.oldest_synced_at,
            "last_error_code": state.last_error_code,
            "last_error_message": state.last_error_message,
            "message": _archive_message(state.status),
        }
    statuses = {state.status for state in states}
    if "running" in statuses:
        status = "running"
    elif "failed" in statuses:
        status = "failed"
    elif "partial" in statuses:
        status = "partial"
    elif statuses == {"complete"}:
        status = "complete"
    else:
        status = "not_started"
    newest = max(
        (state.newest_synced_at for state in states if state.newest_synced_at is not None),
        default=None,
    )
    oldest = min(
        (state.oldest_synced_at for state in states if state.oldest_synced_at is not None),
        default=None,
    )
    return {
        "status": status,
        "is_complete": status == "complete",
        "total_synced_count": sum(state.total_synced_count for state in states),
        "batch_count": sum(state.batch_count for state in states),
        "newest_synced_at": newest,
        "oldest_synced_at": oldest,
        "message": _archive_message(status),
    }


def _email_range_window(
    *,
    user: User,
    range_type: str,
    custom_from: date | None,
    custom_to: date | None,
    now: datetime | None,
) -> tuple[datetime | None, datetime | None, str]:
    resolved_range = (range_type or "all_synced").strip().lower()
    if resolved_range == "all":
        resolved_range = "all_synced"
    if resolved_range not in {"today", "last_7_days", "last_30_days", "custom", "all_synced"}:
        raise EmailServiceError("INVALID_REQUEST", "Unsupported email range.")
    if resolved_range == "all_synced":
        return None, None, resolved_range
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    if resolved_range == "today":
        start, end = _today_window(user.timezone, resolved_now)
        return start, end, resolved_range
    if resolved_range == "last_7_days":
        return resolved_now - timedelta(days=7), resolved_now, resolved_range
    if resolved_range == "last_30_days":
        return resolved_now - timedelta(days=30), resolved_now, resolved_range
    if custom_from is None or custom_to is None:
        raise EmailServiceError(
            "INVALID_REQUEST",
            "Custom range requires from and to dates.",
        )
    if custom_from > custom_to:
        raise EmailServiceError("INVALID_REQUEST", "Custom range is invalid.")
    user_zone = _user_zone_for_email(user.timezone)
    start = datetime.combine(custom_from, time.min, tzinfo=user_zone).astimezone(UTC)
    end = datetime.combine(custom_to, time.max, tzinfo=user_zone).astimezone(UTC)
    return start, end, resolved_range


def _user_zone_for_email(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo(get_settings().default_timezone)


def _archive_message(status: str) -> str:
    if status == "running":
        return "Local archive is still syncing. Results may be incomplete."
    if status == "partial":
        return "Local archive is partially synced. Resume to continue backfilling older mail."
    if status == "failed":
        return "Local archive sync failed. Retry to continue from the saved checkpoint."
    if status == "complete":
        return "Local archive sync is complete."
    return "Local archive has not started."


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
    try:
        mailbox_provider = provider or get_mailbox_provider(mailbox.provider)
    except ProviderRegistryError as exc:
        raise EmailServiceError(exc.code, exc.message, exc.status_code) from exc
    if mailbox.permission_mode != "write_enabled":
        raise EmailServiceError("FORBIDDEN", "Mailbox is read-only.", 403)
    if "https://www.googleapis.com/auth/gmail.modify" not in (mailbox.granted_scopes or []):
        raise EmailServiceError("FORBIDDEN", "Mailbox does not have Gmail modify scope.", 403)

    action_type = "mark_read" if read else "mark_unread"
    before_state = _email_read_state_snapshot(email)
    try:
        refresh_token = _decrypt_refresh_token(db, mailbox_id=mailbox.id)
        access_token = mailbox_provider.refresh_access_token(refresh_token)
        labels = (
            mailbox_provider.mark_as_read(access_token, email.external_id)
            if read
            else mailbox_provider.mark_as_unread(access_token, email.external_id)
        )
    except EmailServiceError as exc:
        record_failed_action(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
            email_id=email.id,
            action_type=action_type,
            source="email_detail",
            provider_effect="gmail_synced",
            before_state=before_state,
            error_code=exc.code,
            error_message=exc.message,
            now=now,
        )
        db.flush()
        raise
    except ProviderError as exc:
        record_failed_action(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
            email_id=email.id,
            action_type=action_type,
            source="email_detail",
            provider_effect="gmail_synced",
            before_state=before_state,
            error_code=exc.code,
            error_message=exc.message,
            now=now,
        )
        db.flush()
        raise EmailServiceError(exc.code, exc.message, exc.status_code) from exc

    email.is_read = read
    email.provider_labels = labels or _local_labels_after_read_state(
        email.provider_labels, read=read
    )
    resolved_now = now or datetime.now(UTC)
    email.last_synced_at = resolved_now
    email.updated_at = resolved_now
    record_completed_action(
        db,
        user_id=user.id,
        mailbox_id=mailbox.id,
        email_id=email.id,
        action_type=action_type,
        source="email_detail",
        provider_effect="gmail_synced",
        before_state=before_state,
        after_state=_email_read_state_snapshot(email),
        now=resolved_now,
    )
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


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _email_read_state_snapshot(email: Email) -> dict[str, object]:
    return {
        "is_read": email.is_read,
        "provider_labels": list(email.provider_labels or []),
    }
