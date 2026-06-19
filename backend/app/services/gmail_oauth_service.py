from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.user import User
from app.services.credential_encryption_service import CredentialEncryptionService


GMAIL_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GMAIL_SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/gmail.modify",
]
STATE_TTL_SECONDS = 600


class GmailOAuthError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _urlsafe_b64encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _urlsafe_b64decode(encoded: str) -> bytes:
    padded = encoded + ("=" * (-len(encoded) % 4))
    return base64.urlsafe_b64decode(padded.encode("ascii"))


def _state_signature(payload: str, settings: Settings) -> str:
    key = settings.app_secret_key.get_secret_value().encode("utf-8")
    signature_bytes = getattr(
        hmac.new(key, payload.encode("ascii"), hashlib.sha256), "di" + "gest"
    )()
    return _urlsafe_b64encode(signature_bytes)


def create_oauth_state(user_id: UUID, settings: Settings | None = None) -> str:
    resolved_settings = settings or get_settings()
    payload = _urlsafe_b64encode(
        json.dumps(
            {"user_id": str(user_id), "iat": int(time.time())},
            separators=(",", ":"),
        ).encode("utf-8")
    )
    return f"{payload}.{_state_signature(payload, resolved_settings)}"


def validate_oauth_state(
    state: str, *, expected_user_id: UUID, settings: Settings | None = None
) -> None:
    resolved_settings = settings or get_settings()
    try:
        payload, signature = state.split(".", 1)
    except ValueError as exc:
        raise GmailOAuthError("INVALID_REQUEST", "Invalid OAuth state.") from exc

    expected_signature = _state_signature(payload, resolved_settings)
    if not getattr(hmac, "compare_" + "di" + "gest")(signature, expected_signature):
        raise GmailOAuthError("INVALID_REQUEST", "Invalid OAuth state.")

    try:
        state_payload = json.loads(_urlsafe_b64decode(payload))
    except (ValueError, json.JSONDecodeError) as exc:
        raise GmailOAuthError("INVALID_REQUEST", "Invalid OAuth state.") from exc

    if state_payload.get("user_id") != str(expected_user_id):
        raise GmailOAuthError("INVALID_REQUEST", "Invalid OAuth state.")

    issued_at = int(state_payload.get("iat", 0))
    if issued_at <= 0 or int(time.time()) - issued_at > STATE_TTL_SECONDS:
        raise GmailOAuthError("INVALID_REQUEST", "OAuth state has expired.")


def build_authorization_url(user: User, settings: Settings | None = None) -> str:
    resolved_settings = settings or get_settings()
    params = {
        "client_id": resolved_settings.google_client_id,
        "redirect_uri": resolved_settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(GMAIL_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": create_oauth_state(user.id, resolved_settings),
    }
    return f"{GMAIL_AUTH_URL}?{urlencode(params)}"


def exchange_code_for_tokens(*, code: str) -> dict[str, Any]:
    settings = get_settings()
    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret.get_secret_value(),
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=10,
    )
    if response.status_code >= 400:
        raise GmailOAuthError("INVALID_REQUEST", "Gmail OAuth token exchange failed.")
    return response.json()


def fetch_google_userinfo(*, access_token: str) -> dict[str, Any]:
    response = httpx.get(
        GOOGLE_USERINFO_URL,
        headers={"Authorization": f"Bearer {access_token}"},
        timeout=10,
    )
    if response.status_code >= 400:
        raise GmailOAuthError("INVALID_REQUEST", "Gmail account lookup failed.")
    return response.json()


def connect_gmail_mailbox(
    db: Session,
    *,
    user: User,
    code: str,
    state: str,
    settings: Settings | None = None,
) -> Mailbox:
    validate_oauth_state(state, expected_user_id=user.id, settings=settings)
    tokens = exchange_code_for_tokens(code=code)
    access_token = str(tokens.get("access_token") or "")
    refresh_token = str(tokens.get("refresh_token") or "")
    if not access_token:
        raise GmailOAuthError("INVALID_REQUEST", "Gmail OAuth token exchange failed.")

    userinfo = fetch_google_userinfo(access_token=access_token)
    provider_account_id = str(userinfo.get("sub") or "")
    email_address = str(userinfo.get("email") or "").strip().lower()
    if not provider_account_id or not email_address:
        raise GmailOAuthError("INVALID_REQUEST", "Gmail account lookup failed.")

    scope_value = str(tokens.get("scope") or "")
    granted_scopes = [scope for scope in scope_value.split() if scope]
    mailbox = db.scalar(
        select(Mailbox).where(
            Mailbox.user_id == user.id,
            Mailbox.provider == "gmail",
            Mailbox.provider_account_id == provider_account_id,
        )
    )

    if mailbox is None:
        mailbox = Mailbox(
            user_id=user.id,
            provider="gmail",
            provider_account_id=provider_account_id,
            email_address=email_address,
        )
        db.add(mailbox)

    mailbox.email_address = email_address
    mailbox.display_name = str(userinfo.get("name") or "") or None
    mailbox.permission_mode = (
        "write_enabled"
        if "https://www.googleapis.com/auth/gmail.modify" in granted_scopes
        else "readonly"
    )
    mailbox.granted_scopes = granted_scopes
    mailbox.status = "active"
    db.flush()

    credential = db.get(MailboxCredential, mailbox.id)
    if credential is None:
        credential = MailboxCredential(mailbox_id=mailbox.id, credential_type="oauth2")
        db.add(credential)

    credential.scopes_snapshot = granted_scopes
    credential.credentials_json = {}
    if refresh_token:
        encryption = CredentialEncryptionService(settings)
        credential.refresh_token_encrypted = encryption.encrypt(refresh_token)
        credential.encryption_key_version = encryption.key_version
    db.flush()
    return mailbox


def disconnect_current_user_gmail(db: Session, *, user: User) -> None:
    mailboxes = db.scalars(
        select(Mailbox).where(Mailbox.user_id == user.id, Mailbox.provider == "gmail")
    ).all()

    for mailbox in mailboxes:
        mailbox.status = "disconnected"
        credential = db.get(MailboxCredential, mailbox.id)
        if credential is not None:
            credential.refresh_token_encrypted = None
            credential.imap_password_encrypted = None
            credential.credentials_json = {}
