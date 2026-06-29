from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol


class ProviderError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


@dataclass(slots=True)
class ProviderCapabilities:
    can_mark_read: bool
    can_mark_unread: bool
    can_fetch_body: bool
    can_fetch_thread: bool
    can_archive: bool
    can_label: bool
    supports_oauth: bool
    supports_password_auth: bool
    supports_folders: bool

    def as_dict(self) -> dict[str, bool]:
        return {
            "can_mark_read": self.can_mark_read,
            "can_mark_unread": self.can_mark_unread,
            "can_fetch_body": self.can_fetch_body,
            "can_fetch_thread": self.can_fetch_thread,
            "can_archive": self.can_archive,
            "can_label": self.can_label,
            "supports_oauth": self.supports_oauth,
            "supports_password_auth": self.supports_password_auth,
            "supports_folders": self.supports_folders,
        }


class MailboxProvider(Protocol):
    provider_key: str

    def get_capabilities(self) -> ProviderCapabilities:
        raise NotImplementedError

    def refresh_access_token(self, refresh_token: str) -> str:
        raise NotImplementedError

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list["ProviderEmailMessage"]:
        raise NotImplementedError

    def list_archive_batch(
        self,
        access_token: str,
        *,
        cursor: dict[str, Any] | None,
        batch_size: int,
    ) -> "ProviderArchiveBatch":
        raise NotImplementedError

    def get_message_detail(
        self,
        access_token: str,
        message_id: str,
    ) -> "ProviderEmailMessage":
        raise NotImplementedError

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        raise NotImplementedError

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        raise NotImplementedError


@dataclass(slots=True)
class ProviderEmailMessage:
    external_id: str
    external_thread_id: str | None
    internet_message_id: str | None
    subject: str | None
    from_name: str | None
    from_address: str | None
    to_addresses: list[str]
    cc_addresses: list[str]
    snippet: str | None
    body_text: str | None
    body_text_truncated: bool
    received_at: datetime
    is_read: bool
    provider_labels: list[str]
    gmail_history_id: str | None
    raw_payload_hash: str


@dataclass(slots=True)
class ProviderArchiveBatch:
    messages: list[ProviderEmailMessage]
    cursor: dict[str, Any] | None
    is_complete: bool
