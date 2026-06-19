from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


class ProviderError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 502) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


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
