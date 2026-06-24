from __future__ import annotations

from datetime import datetime

from app.providers.base import ProviderCapabilities, ProviderEmailMessage, ProviderError


class OutlookProvider:
    provider_key = "outlook"

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            can_mark_read=False,
            can_mark_unread=False,
            can_fetch_body=False,
            can_fetch_thread=False,
            can_archive=False,
            can_label=False,
            supports_oauth=True,
            supports_password_auth=False,
            supports_folders=True,
        )

    def refresh_access_token(self, refresh_token: str) -> str:
        raise ProviderError(
            "outlook_not_configured",
            "Outlook provider is not configured.",
            400,
        )

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        raise ProviderError(
            "outlook_not_configured",
            "Outlook provider is not configured.",
            400,
        )

    def get_message_detail(
        self,
        access_token: str,
        message_id: str,
    ) -> ProviderEmailMessage:
        raise ProviderError(
            "outlook_not_configured",
            "Outlook provider is not configured.",
            400,
        )

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        raise ProviderError(
            "outlook_not_configured",
            "Outlook provider is not configured.",
            400,
        )

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        raise ProviderError(
            "outlook_not_configured",
            "Outlook provider is not configured.",
            400,
        )
