from urllib.parse import urlencode

from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import Settings, get_settings
from app.db.models.user import User
from app.services.gmail_oauth_service import (
    GmailOAuthError,
    build_authorization_url,
    connect_gmail_mailbox,
    disconnect_current_user_gmail,
)


router = APIRouter(prefix="/api/auth/gmail", tags=["gmail-oauth"])


def _mailbox_settings_redirect(
    settings: Settings,
    *,
    gmail: str,
    code: str | None = None,
    mailbox_id: object | None = None,
) -> RedirectResponse:
    params = {"gmail": gmail}
    if code:
        params["code"] = code
    if mailbox_id:
        params["mailbox_id"] = str(mailbox_id)

    base_url = settings.frontend_base_url.rstrip("/")
    return RedirectResponse(
        f"{base_url}/settings/mailboxes?{urlencode(params)}",
        status_code=303,
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
) -> RedirectResponse:
    if error:
        return _mailbox_settings_redirect(
            settings,
            gmail="error",
            code="INVALID_REQUEST",
        )
    if not code or not state:
        return _mailbox_settings_redirect(
            settings,
            gmail="error",
            code="INVALID_REQUEST",
        )

    try:
        mailbox = connect_gmail_mailbox(
            db, user=current_user, code=code, state=state, settings=settings
        )
    except GmailOAuthError as exc:
        return _mailbox_settings_redirect(
            settings,
            gmail="error",
            code=exc.code,
        )

    return _mailbox_settings_redirect(
        settings,
        gmail="connected",
        mailbox_id=mailbox.id,
    )


@router.post("/disconnect")
def gmail_disconnect(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    disconnect_current_user_gmail(db, user=current_user)
    return {"data": {}, "meta": {}}
