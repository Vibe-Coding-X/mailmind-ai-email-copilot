from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.db.models.user import User
from app.schemas.digest import digest_payload
from app.services.digest_service import (
    DigestServiceError,
    generate_today_digest,
    get_digest,
    get_today_digest,
    refresh_today_digest,
)


router = APIRouter(prefix="/api/digest", tags=["digest"])


def _raise_digest_error(error: DigestServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(
            error.code,
            error.message,
            retryable=error.retryable,
        )["error"],
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
