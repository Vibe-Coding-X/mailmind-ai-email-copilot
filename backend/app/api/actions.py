from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.db.models.user import User
from app.schemas.user_action import user_action_payload
from app.services.user_action_service import (
    UserActionServiceError,
    create_action,
    get_user_action,
    list_digest_item_actions,
    query_user_actions,
)


router = APIRouter(prefix="/api/actions", tags=["actions"])


class CreateActionRequest(BaseModel):
    mailbox_id: UUID
    action_type: str
    source: str = "dashboard"
    provider_effect: str = "none"
    digest_id: UUID | None = None
    digest_item_id: UUID | None = None
    email_id: UUID | None = None
    before_state: dict[str, object] = Field(default_factory=dict)
    after_state: dict[str, object] = Field(default_factory=dict)


def _raise_action_error(error: UserActionServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(error.code, error.message)["error"],
    )


@router.post("")
def create_user_action(
    request: CreateActionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        action = create_action(
            db,
            user_id=current_user.id,
            mailbox_id=request.mailbox_id,
            digest_id=request.digest_id,
            digest_item_id=request.digest_item_id,
            email_id=request.email_id,
            action_type=request.action_type,
            action_status="executed",
            source=request.source,
            provider_effect=request.provider_effect,
            before_state=request.before_state,
            after_state=request.after_state,
        )
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {"data": {"action": user_action_payload(action, detail=True)}, "meta": {}}


@router.get("")
def list_actions(
    limit: int = 50,
    offset: int = 0,
    action_type: str | None = None,
    status: str | None = None,
    provider_effect: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    related_resource_type: str | None = None,
    related_resource_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        result = query_user_actions(
            db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            action_type=action_type,
            status=status,
            provider_effect=provider_effect,
            created_from=created_from,
            created_to=created_to,
            related_resource_type=related_resource_type,
            related_resource_id=related_resource_id,
        )
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {
        "data": {
            "actions": [user_action_payload(action) for action in result.actions],
            "pagination": {
                "limit": result.limit,
                "offset": result.offset,
                "count": len(result.actions),
                "has_more": result.has_more,
            },
        },
        "meta": {"limit": result.limit, "offset": result.offset},
    }


@router.get("/digest-items/{item_id}")
def get_digest_item_actions(
    item_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        actions = list_digest_item_actions(
            db,
            user_id=current_user.id,
            digest_item_id=item_id,
            limit=limit,
        )
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {
        "data": {
            "actions": [user_action_payload(action, detail=True) for action in actions],
        },
        "meta": {"limit": max(1, min(limit, 100))},
    }


@router.get("/{action_id}")
def get_action_detail(
    action_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        action = get_user_action(db, user_id=current_user.id, action_id=action_id)
    except UserActionServiceError as exc:
        _raise_action_error(exc)
    return {"data": {"action": user_action_payload(action, detail=True)}, "meta": {}}
