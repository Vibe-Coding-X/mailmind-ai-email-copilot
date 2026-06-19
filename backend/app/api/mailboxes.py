from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.models.user import User
from app.schemas.mailbox import mailbox_payload
from app.schemas.sync_job import sync_job_payload, sync_status_for_api
from app.services.email_sync_service import EmailSyncError, sync_today_emails


router = APIRouter(prefix="/api/mailboxes", tags=["mailboxes"])


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=404,
        detail=error_response("INVALID_REQUEST", "Mailbox not found.")["error"],
    )


def _get_owned_mailbox(db: Session, *, user: User, mailbox_id: UUID) -> Mailbox:
    mailbox = db.scalar(
        select(Mailbox).where(Mailbox.id == mailbox_id, Mailbox.user_id == user.id)
    )
    if mailbox is None:
        raise _not_found()
    return mailbox


@router.get("")
def list_mailboxes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    mailboxes = db.scalars(
        select(Mailbox)
        .where(Mailbox.user_id == current_user.id)
        .order_by(Mailbox.created_at.asc())
    ).all()
    return {
        "data": {"mailboxes": [mailbox_payload(mailbox) for mailbox in mailboxes]},
        "meta": {},
    }


@router.get("/{mailbox_id}")
def get_mailbox(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    mailbox = _get_owned_mailbox(db, user=current_user, mailbox_id=mailbox_id)
    return {"data": {"mailbox": mailbox_payload(mailbox)}, "meta": {}}


@router.get("/{mailbox_id}/sync-status")
def get_sync_status(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    mailbox = _get_owned_mailbox(db, user=current_user, mailbox_id=mailbox_id)
    last_job = db.scalar(
        select(SyncJob)
        .where(SyncJob.mailbox_id == mailbox.id, SyncJob.user_id == current_user.id)
        .order_by(SyncJob.created_at.desc())
    )
    return {
        "data": {
            "mailbox_id": str(mailbox.id),
            "status": sync_status_for_api(last_job.status) if last_job else "not_started",
            "last_successful_sync_at": mailbox.last_successful_sync_at,
            "last_job": sync_job_payload(last_job),
        },
        "meta": {},
    }


@router.post("/{mailbox_id}/sync")
def trigger_sync(
    mailbox_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    mailbox = _get_owned_mailbox(db, user=current_user, mailbox_id=mailbox_id)
    try:
        result = sync_today_emails(
            db,
            user_id=current_user.id,
            mailbox_id=mailbox.id,
        )
    except EmailSyncError as exc:
        db.commit()
        raise HTTPException(
            status_code=exc.status_code,
            detail=error_response(exc.code, exc.message, retryable=False)["error"],
        ) from exc

    return {
        "data": {
            "mailbox_id": str(result.mailbox_id),
            "status": result.status,
            "synced_count": result.synced_count,
            "job_id": str(result.job_id),
        },
        "meta": {},
    }
