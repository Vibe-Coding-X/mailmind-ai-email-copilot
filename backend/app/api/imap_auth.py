from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.core.config import Settings, get_settings
from app.db.models.user import User
from app.schemas.mailbox import mailbox_payload
from app.services.imap_mailbox_service import ImapMailboxError, connect_imap_mailbox


router = APIRouter(prefix="/api/auth/imap", tags=["imap-auth"])


class ImapConnectRequest(BaseModel):
    account_email: str = Field(min_length=1, max_length=255)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=993, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=4096)
    folder: str = Field(default="INBOX", min_length=1, max_length=255)
    use_ssl: bool = True
    display_name: str | None = Field(default=None, max_length=255)


@router.post("/connect", status_code=201)
def imap_connect(
    payload: ImapConnectRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    try:
        mailbox = connect_imap_mailbox(
            db,
            user=current_user,
            account_email=payload.account_email,
            host=payload.host,
            port=payload.port,
            username=payload.username,
            password=payload.password,
            folder=payload.folder,
            use_ssl=payload.use_ssl,
            display_name=payload.display_name,
            settings=settings,
        )
    except ImapMailboxError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail=error_response(exc.code, exc.message, retryable=False)["error"],
        ) from exc

    return {
        "data": {
            "provider": "imap",
            "mailbox": mailbox_payload(mailbox),
        },
        "meta": {},
    }
