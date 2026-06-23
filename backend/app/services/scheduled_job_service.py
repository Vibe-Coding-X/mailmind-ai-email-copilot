from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, time
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models.daily_digest import DailyDigest
from app.db.models.mailbox import Mailbox
from app.db.models.sync_job import SyncJob
from app.db.models.user import User
from app.services.digest_service import dispatch_digest_job
from app.services.email_sync_service import enqueue_sync_today_job, find_active_email_sync_job


@dataclass(slots=True)
class ScheduledJobEnqueueResult:
    job_ids: list[UUID]
    created_count: int
    skipped_count: int


def enqueue_due_scheduled_email_sync_jobs(
    db: Session,
    *,
    now: datetime | None = None,
    dispatch: bool = True,
) -> ScheduledJobEnqueueResult:
    resolved_now = _ensure_utc(now or datetime.now(UTC))
    created: list[UUID] = []
    skipped = 0

    for user, mailbox in _active_gmail_mailboxes(db):
        target_date = _local_date(user.timezone, resolved_now)
        job_key = f"scheduled_email_sync:{mailbox.id}:{target_date}"
        if _job_key_exists(db, job_key) or find_active_email_sync_job(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
        ):
            skipped += 1
            continue
        result = enqueue_sync_today_job(
            db,
            user_id=user.id,
            mailbox_id=mailbox.id,
            dispatch=dispatch,
            now=resolved_now,
            trigger_source="scheduled",
            job_key=job_key,
        )
        created.append(result.job_id)

    return ScheduledJobEnqueueResult(
        job_ids=created,
        created_count=len(created),
        skipped_count=skipped,
    )


def enqueue_due_scheduled_digest_jobs(
    db: Session,
    *,
    now: datetime | None = None,
    dispatch: bool = True,
    auto_generate: bool | None = None,
    generate_time: str | None = None,
) -> ScheduledJobEnqueueResult:
    settings = get_settings()
    if auto_generate is None:
        auto_generate = settings.digest_auto_generate
    if not auto_generate:
        return ScheduledJobEnqueueResult(job_ids=[], created_count=0, skipped_count=0)

    resolved_now = _ensure_utc(now or datetime.now(UTC))
    scheduled_time = _parse_generate_time(generate_time or settings.digest_generate_time)
    created: list[UUID] = []
    skipped = 0

    for user, mailbox in _active_gmail_mailboxes(db):
        local_now = resolved_now.astimezone(_user_zone(user.timezone))
        target_date = local_now.date()
        if local_now.time().replace(second=0, microsecond=0) < scheduled_time:
            skipped += 1
            continue

        job_key = f"scheduled_digest:{mailbox.id}:{target_date}"
        if _job_key_exists(db, job_key) or _current_digest_exists(
            db,
            mailbox_id=mailbox.id,
            target_date=target_date,
        ):
            skipped += 1
            continue
        job = _create_scheduled_job(
            db,
            user=user,
            mailbox=mailbox,
            job_type="generate_daily_digest",
            job_key=job_key,
            target_date=target_date,
            now=resolved_now,
        )
        if dispatch:
            job.celery_task_id = dispatch_digest_job(job.id)
            db.flush()
        created.append(job.id)

    return ScheduledJobEnqueueResult(
        job_ids=created,
        created_count=len(created),
        skipped_count=skipped,
    )


def _active_gmail_mailboxes(db: Session) -> list[tuple[User, Mailbox]]:
    return list(
        db.execute(
            select(User, Mailbox)
            .join(Mailbox, Mailbox.user_id == User.id)
            .where(
                User.status == "active",
                Mailbox.provider == "gmail",
                Mailbox.status == "active",
            )
            .order_by(User.created_at.asc(), Mailbox.created_at.asc())
        ).all()
    )


def _create_scheduled_job(
    db: Session,
    *,
    user: User,
    mailbox: Mailbox,
    job_type: str,
    job_key: str,
    target_date: object,
    now: datetime,
) -> SyncJob:
    job = SyncJob(
        user_id=user.id,
        mailbox_id=mailbox.id,
        job_type=job_type,
        trigger_source="scheduled",
        job_key=job_key,
        target_date=target_date,
        status="queued",
        retry_count=0,
        payload_json={},
        created_at=now,
    )
    db.add(job)
    db.flush()
    return job


def _job_key_exists(db: Session, job_key: str) -> bool:
    return (
        db.scalar(select(SyncJob.id).where(SyncJob.job_key == job_key).limit(1))
        is not None
    )


def _current_digest_exists(db: Session, *, mailbox_id: UUID, target_date: object) -> bool:
    return (
        db.scalar(
            select(DailyDigest.id)
            .where(
                DailyDigest.mailbox_id == mailbox_id,
                DailyDigest.digest_date == target_date,
                DailyDigest.is_current.is_(True),
            )
            .limit(1)
        )
        is not None
    )


def _local_date(timezone: str, value: datetime) -> object:
    return value.astimezone(_user_zone(timezone)).date()


def _parse_generate_time(value: str) -> time:
    try:
        hour_text, minute_text = value.split(":", 1)
        return time(hour=int(hour_text), minute=int(minute_text))
    except (TypeError, ValueError):
        return time(hour=8, minute=0)


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _user_zone(timezone: str) -> ZoneInfo:
    try:
        return ZoneInfo(timezone)
    except ZoneInfoNotFoundError:
        return ZoneInfo(get_settings().default_timezone)
