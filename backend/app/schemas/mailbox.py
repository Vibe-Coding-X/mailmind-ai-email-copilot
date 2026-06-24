from __future__ import annotations

from typing import Any

from app.db.models.mailbox import Mailbox
from app.providers.registry import get_mailbox_provider


def mailbox_status_for_api(status: str) -> str:
    if status == "active":
        return "connected"
    return status


def mailbox_payload(mailbox: Mailbox) -> dict[str, Any]:
    sync_cursor = mailbox.sync_cursor or None
    provider = mailbox.provider.strip().lower()
    imap_config = mailbox_imap_config_payload(mailbox)
    payload = {
        "id": mailbox.id,
        "provider": provider,
        "provider_preset": mailbox_provider_preset(mailbox, imap_config=imap_config),
        "email_address": mailbox.email_address,
        "account_email": mailbox.email_address,
        "display_name": mailbox.display_name,
        "provider_account_id": mailbox.provider_account_id,
        "status": mailbox_status_for_api(mailbox.status),
        "last_successful_sync_at": mailbox.last_successful_sync_at,
        "last_error_code": None,
        "last_error_message": None,
        "credential_status": mailbox_credential_status(mailbox),
        "capabilities": mailbox_capabilities_payload(provider),
        "sync_cursor": sync_cursor,
        "created_at": mailbox.created_at,
        "updated_at": mailbox.updated_at,
    }
    if imap_config is not None:
        payload["imap_config"] = imap_config
        payload["provider_config"] = {
            "host": imap_config["host"],
            "port": imap_config["port"],
            "use_ssl": imap_config["use_ssl"],
            "default_folder": imap_config["folder"],
            "username": imap_config["username"],
        }
    return payload


def mailbox_capabilities_payload(provider_key: str) -> dict[str, bool]:
    provider = get_mailbox_provider(provider_key)
    return provider.get_capabilities().as_dict()


def mailbox_imap_config_payload(mailbox: Mailbox) -> dict[str, object] | None:
    if mailbox.provider.strip().lower() != "imap" or mailbox.credential is None:
        return None
    config = mailbox.credential.credentials_json or {}
    return {
        "host": str(config.get("host") or ""),
        "port": int(config.get("port") or 993),
        "username": str(config.get("username") or mailbox.email_address),
        "folder": str(config.get("folder") or "INBOX"),
        "use_ssl": bool(config.get("use_ssl", True)),
    }


def mailbox_provider_preset(
    mailbox: Mailbox, *, imap_config: dict[str, object] | None
) -> str:
    provider = mailbox.provider.strip().lower()
    if provider != "imap":
        return provider
    credential_config = mailbox.credential.credentials_json if mailbox.credential else {}
    preset = str(credential_config.get("provider_preset") or "").strip().lower()
    if preset:
        return preset
    host = str((imap_config or {}).get("host") or "").strip().lower()
    if host == "imap.qq.com":
        return "qq"
    if host == "imap.163.com":
        return "163"
    if host == "imap.gmail.com":
        return "gmail_imap"
    return "custom"


def mailbox_credential_status(mailbox: Mailbox) -> str:
    credential = mailbox.credential
    if credential is None:
        return "missing"
    provider = mailbox.provider.strip().lower()
    if provider == "imap":
        return "present" if credential.imap_password_encrypted else "missing"
    if provider in {"gmail", "outlook"}:
        return "present" if credential.refresh_token_encrypted else "missing"
    return "present"
