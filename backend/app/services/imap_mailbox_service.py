from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models.mailbox import Mailbox
from app.db.models.mailbox_credential import MailboxCredential
from app.db.models.user import User
from app.providers.base import ProviderError
from app.providers.imap import ImapMailboxConfig, ImapProvider
from app.services.credential_encryption_service import CredentialEncryptionService


class ImapMailboxError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def connect_imap_mailbox(
    db: Session,
    *,
    user: User,
    account_email: str,
    host: str,
    port: int,
    username: str,
    password: str,
    folder: str = "INBOX",
    use_ssl: bool = True,
    display_name: str | None = None,
    settings: Settings | None = None,
) -> Mailbox:
    config = _build_config(host=host, port=port, username=username, folder=folder, use_ssl=use_ssl)
    normalized_email = _normalize_email(account_email)
    if not normalized_email:
        raise ImapMailboxError("INVALID_REQUEST", "IMAP account email is required.")
    if not password:
        raise ImapMailboxError("INVALID_REQUEST", "IMAP password is required.")

    try:
        ImapProvider(config=config).check_connection(password)
    except ProviderError as exc:
        raise ImapMailboxError(exc.code, exc.message, exc.status_code) from exc

    provider_account_id = f"{config.host}:{config.port}:{config.username}"
    mailbox = db.scalar(
        select(Mailbox).where(
            Mailbox.user_id == user.id,
            Mailbox.provider == "imap",
            Mailbox.provider_account_id == provider_account_id,
        )
    )
    if mailbox is None:
        mailbox = Mailbox(
            user_id=user.id,
            provider="imap",
            provider_account_id=provider_account_id,
            email_address=normalized_email,
        )
        db.add(mailbox)

    mailbox.email_address = normalized_email
    mailbox.display_name = display_name.strip() if display_name and display_name.strip() else None
    mailbox.permission_mode = "write_enabled"
    mailbox.granted_scopes = []
    mailbox.status = "active"
    db.flush()

    credential = db.get(MailboxCredential, mailbox.id)
    if credential is None:
        credential = MailboxCredential(
            mailbox_id=mailbox.id,
            credential_type="imap_password",
        )
        db.add(credential)

    encryption = CredentialEncryptionService(settings)
    credential.credential_type = "imap_password"
    credential.refresh_token_encrypted = None
    credential.imap_password_encrypted = encryption.encrypt(password)
    credential.scopes_snapshot = []
    credential.credentials_json = {
        "provider_preset": _provider_preset_for_host(config.host),
        "host": config.host,
        "port": config.port,
        "username": config.username,
        "folder": config.folder,
        "use_ssl": config.use_ssl,
    }
    credential.encryption_key_version = encryption.key_version
    db.flush()
    return mailbox


def _build_config(
    *,
    host: str,
    port: int,
    username: str,
    folder: str,
    use_ssl: bool,
) -> ImapMailboxConfig:
    normalized_host = host.strip().lower()
    normalized_username = username.strip()
    normalized_folder = folder.strip() or "INBOX"
    if not normalized_host:
        raise ImapMailboxError("INVALID_REQUEST", "IMAP host is required.")
    if not normalized_username:
        raise ImapMailboxError("INVALID_REQUEST", "IMAP username is required.")
    if port < 1 or port > 65535:
        raise ImapMailboxError("INVALID_REQUEST", "IMAP port is invalid.")
    return ImapMailboxConfig(
        host=normalized_host,
        port=port,
        username=normalized_username,
        folder=normalized_folder,
        use_ssl=use_ssl,
    )


def _normalize_email(value: str) -> str:
    return value.strip().lower()


def _provider_preset_for_host(host: str) -> str:
    normalized = host.strip().lower()
    if normalized == "imap.qq.com":
        return "qq"
    if normalized == "imap.163.com":
        return "163"
    if normalized == "imap.gmail.com":
        return "gmail_imap"
    return "custom"
