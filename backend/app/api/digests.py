from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.db.models.user import User
from app.schemas.digest import digest_payload
from app.schemas.user_action import user_action_payload
from app.services.digest_service import (
    DigestServiceError,
    generate_today_digest,
    get_digest,
    get_today_digest,
    refresh_today_digest,
)
from app.services.user_action_service import (
    UserActionServiceError,
    record_digest_item_action,
)


router = APIRouter(prefix="/api/digest", tags=["digest"])


class SnoozeDigestItemRequest(BaseModel):
    snoozed_until: str


def _raise_digest_error(error: DigestServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(
            error.code,
            error.message,
            retryable=error.retryable,
        )["error"],
    )


def _raise_action_error(error: UserActionServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(error.code, error.message)["error"],
    )


@router.get("/today")
def read_today_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        digest = get_today_digest(db, user_id=current_user.id)
    except DigestServiceError as exc:
        _raise_digest_error(exc)
    return {"data": {"digest": digest_payload(digest)}, "meta": {}}


@router.post("/today/generate")
def generate_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        digest = generate_today_digest(db, user_id=current_user.id)
    except DigestServiceError as exc:
        db.commit()
        _raise_digest_error(exc)
    return {"data": {"digest": digest_payload(digest)}, "meta": {}}


@router.post("/today/refresh")
def refresh_digest(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        digest = refresh_today_digest(db, user_id=current_user.id)
    except DigestServiceError as exc:
        db.commit()
        _raise_digest_error(exc)
    return {"data": {"digest": digest_payload(digest)}, "meta": {}}


@router.post("/items/{item_id}/mark-done")
def mark_digest_item_done(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        action = record_digest_item_action(
            db,
            user_id=current_user.id,
            item_id=item_id,
            action_type="mark_done",
            after_state={"status": "done"},
        )
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {"data": {"action": user_action_payload(action, detail=True)}, "meta": {}}


@router.post("/items/{item_id}/dismiss")
def dismiss_digest_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        action = record_digest_item_action(
            db,
            user_id=current_user.id,
            item_id=item_id,
            action_type="dismiss_item",
            after_state={"status": "dismissed"},
        )
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {"data": {"action": user_action_payload(action, detail=True)}, "meta": {}}


@router.post("/items/{item_id}/snooze")
def snooze_digest_item(
    item_id: UUID,
    request: SnoozeDigestItemRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        action = record_digest_item_action(
            db,
            user_id=current_user.id,
            item_id=item_id,
            action_type="snooze_item",
            after_state={"snoozed_until": request.snoozed_until},
        )
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {"data": {"action": user_action_payload(action, detail=True)}, "meta": {}}


@router.get("/{digest_id}")
def read_digest(
    digest_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        digest = get_digest(db, user_id=current_user.id, digest_id=digest_id)
    except DigestServiceError as exc:
        _raise_digest_error(exc)
    return {"data": {"digest": digest_payload(digest)}, "meta": {}}
