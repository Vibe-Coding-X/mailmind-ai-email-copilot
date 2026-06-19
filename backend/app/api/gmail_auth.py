from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import error_response, get_current_user, get_db
from app.core.config import Settings, get_settings
from app.db.models.user import User
from app.schemas.mailbox import mailbox_payload
from app.services.gmail_oauth_service import (
    GmailOAuthError,
    build_authorization_url,
    connect_gmail_mailbox,
    disconnect_current_user_gmail,
)


router = APIRouter(prefix="/api/auth/gmail", tags=["gmail-oauth"])


def _raise_gmail_error(error: GmailOAuthError) -> None:
    raise HTTPException(
        status_code=error.status_code,
        detail=error_response(error.code, error.message)["error"],
    )


@router.get("/login")
def gmail_login(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    return {
        "data": {
            "authorization_url": build_authorization_url(current_user, settings),
            "provider": "gmail",
        },
        "meta": {},
    }


@router.get("/callback")
def gmail_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    if error:
        _raise_gmail_error(GmailOAuthError("INVALID_REQUEST", "Gmail OAuth was denied."))
    if not code or not state:
        _raise_gmail_error(
            GmailOAuthError("INVALID_REQUEST", "Gmail OAuth callback is missing code or state.")
        )

    try:
        mailbox = connect_gmail_mailbox(
            db, user=current_user, code=code, state=state, settings=settings
        )
    except GmailOAuthError as exc:
        _raise_gmail_error(exc)

    return {"data": {"mailbox": mailbox_payload(mailbox)}, "meta": {}}


@router.post("/disconnect")
def gmail_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    disconnect_current_user_gmail(db, user=current_user)
    return {"data": {}, "meta": {}}
