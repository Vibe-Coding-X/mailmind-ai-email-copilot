from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.db.models.user import User
from app.schemas.job import job_payload
from app.services.job_service import JobServiceError, get_job, query_jobs, retry_job


router = APIRouter(prefix="/api/jobs", tags=["jobs"])


def _raise_job_error(error: JobServiceError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(error.code, error.message)["error"],
    )


@router.get("")
def list_jobs(
    limit: int = 50,
    offset: int = 0,
    job_type: str | None = None,
    status: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        result = query_jobs(
            db,
            user_id=current_user.id,
            limit=limit,
            offset=offset,
            job_type=job_type,
            status=status,
            created_from=created_from,
            created_to=created_to,
        )
    except JobServiceError as exc:
        _raise_job_error(exc)
    return {
        "data": {
            "jobs": [job_payload(job) for job in result.jobs],
            "pagination": {
                "limit": result.limit,
                "offset": result.offset,
                "count": len(result.jobs),
                "has_more": result.has_more,
            },
        },
        "meta": {"limit": result.limit, "offset": result.offset},
    }


@router.get("/{job_id}")
def get_job_detail(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        job = get_job(db, user_id=current_user.id, job_id=job_id)
    except JobServiceError as exc:
        _raise_job_error(exc)
    return {"data": {"job": job_payload(job)}, "meta": {}}


@router.post("/{job_id}/retry")
def retry_failed_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    try:
        job = retry_job(db, user_id=current_user.id, job_id=job_id)
    except JobServiceError as exc:
        _raise_job_error(exc)
    return {"data": {"job": job_payload(job)}, "meta": {}}

