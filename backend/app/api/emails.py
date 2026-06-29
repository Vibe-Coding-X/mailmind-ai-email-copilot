from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.db.models.user import User
from app.schemas.email import email_detail_payload, email_summary_payload
from app.services.email_service import (
    EmailServiceError,
    get_owned_email,
    list_emails,
    list_today_emails,
    mark_email_read_state,
)


router = APIRouter(prefix="/api/emails", tags=["emails"])


def _raise_email_error(error: EmailServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(error.code, error.message)["error"],
    )


@router.get("")
def get_emails(
    limit: int = 50,
    offset: int = 0,
    is_read: bool | None = None,
    mailbox_id: UUID | None = None,
    received_from: datetime | None = None,
    received_to: datetime | None = None,
    range_type: str = Query("all_synced", alias="range"),
    custom_from: date | None = Query(None, alias="from"),
    custom_to: date | None = Query(None, alias="to"),
    q: str | None = None,
    sort: str = "received_at_desc",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        result = list_emails(
            db,
            user=current_user,
            limit=limit,
            offset=offset,
            is_read=is_read,
            mailbox_id=mailbox_id,
            received_from=received_from,
            received_to=received_to,
            range_type=range_type,
            custom_from=custom_from,
            custom_to=custom_to,
            q=q,
            sort=sort,
        )
    except EmailServiceError as exc:
        _raise_email_error(exc)

    return {
        "data": {
            "emails": [email_summary_payload(email) for email in result.emails],
            "pagination": {
                "limit": result.limit,
                "offset": result.offset,
                "count": len(result.emails),
                "total": result.total,
                "has_more": result.has_more,
            },
            "range": result.range_type,
            "archive_state": result.archive_state,
        },
        "meta": {},
    }


@router.get("/today")
def get_today_emails(
    sort: str = "received_at_desc",
    is_read: bool | None = None,
    priority: str | None = None,
    source: str = "all",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        emails = list_today_emails(
            db,
            user=current_user,
            sort=sort,
            is_read=is_read,
            priority=priority,
            source=source,
        )
    except EmailServiceError as exc:
        _raise_email_error(exc)

    return {
        "data": {"emails": [email_summary_payload(email) for email in emails]},
        "meta": {},
    }


@router.get("/{email_id}")
def get_email_detail(
    email_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        email = get_owned_email(db, user=current_user, email_id=email_id)
    except EmailServiceError as exc:
        _raise_email_error(exc)
    return {"data": {"email": email_detail_payload(email)}, "meta": {}}


@router.post("/{email_id}/mark-read")
def mark_email_read(
    email_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        email = mark_email_read_state(db, user=current_user, email_id=email_id, read=True)
    except EmailServiceError as exc:
        db.commit()
        _raise_email_error(exc)
    return {"data": {"email": email_summary_payload(email)}, "meta": {}}


@router.post("/{email_id}/mark-unread")
def mark_email_unread(
    email_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        email = mark_email_read_state(db, user=current_user, email_id=email_id, read=False)
    except EmailServiceError as exc:
        db.commit()
        _raise_email_error(exc)
    return {"data": {"email": email_summary_payload(email)}, "meta": {}}
