from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.daily_digest import DailyDigest
from app.db.models.digest_item import DigestItem
from app.db.models.email import Email
from app.db.models.mailbox import Mailbox
from app.db.models.user_action import UserAction


class UserActionServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class UserActionQueryResult:
    actions: list[UserAction]
    limit: int
    offset: int
    has_more: bool


SENSITIVE_KEY_PARTS = {
    "token",
    "authorization",
    "password",
    "secret",
    "api_key",
    "apikey",
    "body_text",
    "raw_payload",
    "mime",
}


def create_action(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
    action_type: str,
    action_status: str = "pending",
    source: str = "dashboard",
    provider_effect: str = "none",
    digest_id: UUID | None = None,
    digest_item_id: UUID | None = None,
    email_id: UUID | None = None,
    before_state: dict[str, object] | None = None,
    after_state: dict[str, object] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    now: datetime | None = None,
) -> UserAction:
    _ensure_mailbox_owner(db, user_id=user_id, mailbox_id=mailbox_id)
    digest_id, digest_item_id, email_id = _normalize_and_validate_scope(
        db,
        user_id=user_id,
        mailbox_id=mailbox_id,
        digest_id=digest_id,
        digest_item_id=digest_item_id,
        email_id=email_id,
    )
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    action = UserAction(
        user_id=user_id,
        mailbox_id=mailbox_id,
        digest_id=digest_id,
        digest_item_id=digest_item_id,
        email_id=email_id,
        action_type=action_type,
        action_status=action_status,
        source=source,
        provider_effect=provider_effect,
        before_state=sanitize_audit_state(before_state or {}),
        after_state=sanitize_audit_state(after_state or {}),
        error_code=error_code,
        error_message=_safe_error_message(error_message),
        created_at=resolved_now,
        executed_at=resolved_now if action_status in {"executed", "failed", "cancelled"} else None,
    )
    db.add(action)
    db.flush()
    return action


def record_completed_action(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
    action_type: str,
    source: str = "dashboard",
    provider_effect: str = "none",
    digest_id: UUID | None = None,
    digest_item_id: UUID | None = None,
    email_id: UUID | None = None,
    before_state: dict[str, object] | None = None,
    after_state: dict[str, object] | None = None,
    now: datetime | None = None,
) -> UserAction:
    return create_action(
        db,
        user_id=user_id,
        mailbox_id=mailbox_id,
        digest_id=digest_id,
        digest_item_id=digest_item_id,
        email_id=email_id,
        action_type=action_type,
        action_status="executed",
        source=source,
        provider_effect=provider_effect,
        before_state=before_state,
        after_state=after_state,
        now=now,
    )


def record_failed_action(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
    action_type: str,
    source: str = "dashboard",
    provider_effect: str = "none",
    digest_id: UUID | None = None,
    digest_item_id: UUID | None = None,
    email_id: UUID | None = None,
    before_state: dict[str, object] | None = None,
    after_state: dict[str, object] | None = None,
    error_code: str | None = None,
    error_message: str | None = None,
    now: datetime | None = None,
) -> UserAction:
    return create_action(
        db,
        user_id=user_id,
        mailbox_id=mailbox_id,
        digest_id=digest_id,
        digest_item_id=digest_item_id,
        email_id=email_id,
        action_type=action_type,
        action_status="failed",
        source=source,
        provider_effect=provider_effect,
        before_state=before_state,
        after_state=after_state,
        error_code=error_code,
        error_message=error_message,
        now=now,
    )


def list_user_actions(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 50,
    action_type: str | None = None,
    status: str | None = None,
) -> list[UserAction]:
    resolved_limit = max(1, min(limit, 100))
    statement = (
        select(UserAction)
        .where(UserAction.user_id == user_id)
        .order_by(UserAction.created_at.desc())
        .limit(resolved_limit)
    )
    if action_type is not None:
        statement = statement.where(UserAction.action_type == action_type)
    if status is not None:
        statement = statement.where(UserAction.action_status == status)
    return list(db.scalars(statement).all())


def query_user_actions(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
    action_type: str | None = None,
    status: str | None = None,
    provider_effect: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    related_resource_type: str | None = None,
    related_resource_id: UUID | None = None,
) -> UserActionQueryResult:
    resolved_limit = max(1, min(limit, 100))
    resolved_offset = max(0, offset)
    statement = select(UserAction).where(UserAction.user_id == user_id)
    if action_type is not None:
        statement = statement.where(UserAction.action_type == action_type)
    if status is not None:
        statement = statement.where(UserAction.action_status == status)
    if provider_effect is not None:
        statement = statement.where(UserAction.provider_effect == provider_effect)
    if created_from is not None:
        statement = statement.where(UserAction.created_at >= _ensure_utc(created_from))
    if created_to is not None:
        statement = statement.where(UserAction.created_at <= _ensure_utc(created_to))
    if related_resource_type is not None or related_resource_id is not None:
        if related_resource_type is None or related_resource_id is None:
            raise UserActionServiceError(
                "INVALID_REQUEST",
                "related_resource_type and related_resource_id are required together.",
            )
        statement = statement.where(
            _related_resource_column(related_resource_type) == related_resource_id
        )

    rows = list(
        db.scalars(
            statement.order_by(UserAction.created_at.desc(), UserAction.id.desc())
            .offset(resolved_offset)
            .limit(resolved_limit + 1)
        ).all()
    )
    return UserActionQueryResult(
        actions=rows[:resolved_limit],
        limit=resolved_limit,
        offset=resolved_offset,
        has_more=len(rows) > resolved_limit,
    )


def list_digest_item_actions(
    db: Session,
    *,
    user_id: UUID,
    digest_item_id: UUID,
    limit: int = 50,
) -> list[UserAction]:
    get_owned_digest_item(db, user_id=user_id, item_id=digest_item_id)
    resolved_limit = max(1, min(limit, 100))
    statement = (
        select(UserAction)
        .where(
            UserAction.user_id == user_id,
            UserAction.digest_item_id == digest_item_id,
        )
        .order_by(UserAction.created_at.desc())
        .limit(resolved_limit)
    )
    return list(db.scalars(statement).all())


def _related_resource_column(related_resource_type: str):
    columns = {
        "mailbox": UserAction.mailbox_id,
        "email": UserAction.email_id,
        "digest": UserAction.digest_id,
        "digest_item": UserAction.digest_item_id,
    }
    column = columns.get(related_resource_type)
    if column is None:
        raise UserActionServiceError(
            "INVALID_REQUEST",
            "Unsupported related_resource_type.",
        )
    return column


def get_user_action(db: Session, *, user_id: UUID, action_id: UUID) -> UserAction:
    action = db.scalar(
        select(UserAction).where(UserAction.id == action_id, UserAction.user_id == user_id)
    )
    if action is None:
        raise UserActionServiceError("INVALID_REQUEST", "Action not found.", 404)
    return action


def get_owned_digest_item(db: Session, *, user_id: UUID, item_id: UUID) -> DigestItem:
    item = db.scalar(
        select(DigestItem).where(DigestItem.id == item_id, DigestItem.user_id == user_id)
    )
    if item is None:
        raise UserActionServiceError("INVALID_REQUEST", "Digest item not found.", 404)
    return item


def record_digest_item_action(
    db: Session,
    *,
    user_id: UUID,
    item_id: UUID,
    action_type: str,
    after_state: dict[str, object] | None = None,
    now: datetime | None = None,
) -> UserAction:
    item = get_owned_digest_item(db, user_id=user_id, item_id=item_id)
    return record_completed_action(
        db,
        user_id=user_id,
        mailbox_id=item.mailbox_id,
        digest_id=item.digest_id,
        digest_item_id=item.id,
        email_id=item.email_id,
        action_type=action_type,
        source="dashboard",
        provider_effect="local_only",
        before_state={
            "section": item.section,
            "item_type": item.item_type,
            "suggested_action": item.suggested_action,
        },
        after_state=after_state or {},
        now=now,
    )


def sanitize_audit_state(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        for key, nested_value in value.items():
            lowered = str(key).lower()
            if any(part in lowered for part in SENSITIVE_KEY_PARTS):
                continue
            sanitized[str(key)] = sanitize_audit_state(nested_value)
        return sanitized
    if isinstance(value, list):
        return [sanitize_audit_state(item) for item in value]
    return value


def _ensure_mailbox_owner(db: Session, *, user_id: UUID, mailbox_id: UUID) -> None:
    mailbox = db.scalar(
        select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.user_id == user_id)
    )
    if mailbox is None:
        raise UserActionServiceError("INVALID_REQUEST", "Mailbox not found.", 404)


def _normalize_and_validate_scope(
    db: Session,
    *,
    user_id: UUID,
    mailbox_id: UUID,
    digest_id: UUID | None,
    digest_item_id: UUID | None,
    email_id: UUID | None,
) -> tuple[UUID | None, UUID | None, UUID | None]:
    if digest_id is not None:
        digest = db.scalar(
            select(DailyDigest).where(
                DailyDigest.id == digest_id,
                DailyDigest.user_id == user_id,
                DailyDigest.mailbox_id == mailbox_id,
            )
        )
        if digest is None:
            raise UserActionServiceError("INVALID_REQUEST", "Digest not found.", 404)

    if email_id is not None:
        email = db.scalar(
            select(Email).where(
                Email.id == email_id,
                Email.user_id == user_id,
                Email.mailbox_id == mailbox_id,
            )
        )
        if email is None:
            raise UserActionServiceError("INVALID_REQUEST", "Email not found.", 404)

    if digest_item_id is not None:
        item = db.scalar(
            select(DigestItem).where(
                DigestItem.id == digest_item_id,
                DigestItem.user_id == user_id,
                DigestItem.mailbox_id == mailbox_id,
            )
        )
        if item is None:
            raise UserActionServiceError("INVALID_REQUEST", "Digest item not found.", 404)
        if digest_id is not None and item.digest_id != digest_id:
            raise UserActionServiceError("INVALID_REQUEST", "Digest item not found.", 404)
        if email_id is not None and item.email_id is not None and item.email_id != email_id:
            raise UserActionServiceError("INVALID_REQUEST", "Digest item not found.", 404)
        digest_id = item.digest_id
        email_id = email_id or item.email_id

    return digest_id, digest_item_id, email_id


def _safe_error_message(message: str | None) -> str | None:
    if message is None:
        return None
    sanitized = str(sanitize_audit_state({"message": message}).get("message", ""))
    return sanitized[:500]


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
