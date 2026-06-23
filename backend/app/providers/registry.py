from __future__ import annotations

from app.providers.base import MailboxProvider
from app.providers.gmail import GmailProvider
from app.providers.imap import ImapProvider


class ProviderRegistryError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def get_mailbox_provider(provider_key: str) -> MailboxProvider:
    normalized = provider_key.strip().lower()
    if normalized == GmailProvider.provider_key:
        return GmailProvider()
    if normalized == ImapProvider.provider_key:
        return ImapProvider()
    raise ProviderRegistryError(
        "unsupported_mailbox_provider",
        "Unsupported mailbox provider.",
        400,
    )
