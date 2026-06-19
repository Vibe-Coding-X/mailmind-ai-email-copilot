from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.core.config import Settings, get_settings
from app.providers.base import ProviderEmailMessage, ProviderError
from app.utils.email_parser import parse_gmail_message


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailProvider:
    def __init__(self, *, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or httpx

    def refresh_access_token(self, refresh_token: str) -> str:
        response = self.client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": self.settings.google_client_id,
                "client_secret": self.settings.google_client_secret.get_secret_value(),
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=10,
        )
        self._raise_for_response(response, auth_operation=True)
        payload = response.json()
        access_token = str(payload.get("access_token") or "")
        if not access_token:
            raise ProviderError(
                "MAILBOX_REAUTH_REQUIRED",
                "Gmail access token refresh failed.",
                401,
            )
        return access_token

    def list_today_messages(
        self,
        access_token: str,
        *,
        timezone: str,
        now: datetime | None = None,
    ) -> list[ProviderEmailMessage]:
        resolved_now = now or datetime.now(UTC)
        try:
            user_zone = ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            user_zone = ZoneInfo(self.settings.default_timezone)
        local_now = resolved_now.astimezone(user_zone)
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        return self.list_messages_for_window(
            access_token,
            window_start=local_start.astimezone(UTC),
            window_end=resolved_now.astimezone(UTC),
        )

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        message_ids = self._list_message_ids_for_window(
            access_token, window_start=window_start, window_end=window_end
        )
        messages = [
            self.get_message_detail(access_token, message_id) for message_id in message_ids
        ]
        return [
            message
            for message in messages
            if window_start <= message.received_at <= window_end
        ]

    def get_message_detail(self, access_token: str, message_id: str) -> ProviderEmailMessage:
        response = self.client.get(
            f"{GMAIL_API_BASE_URL}/messages/{message_id}",
            headers=self._headers(access_token),
            params={"format": "full"},
            timeout=10,
        )
        self._raise_for_response(response)
        return parse_gmail_message(response.json())

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        return self._modify_labels(
            access_token,
            message_id,
            payload={"removeLabelIds": ["UNREAD"]},
        )

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        return self._modify_labels(
            access_token,
            message_id,
            payload={"addLabelIds": ["UNREAD"]},
        )

    def _list_message_ids_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[str]:
        after_date = window_start.astimezone(UTC).date()
        before_date = window_end.astimezone(UTC).date() + timedelta(days=1)
        query = f"after:{after_date:%Y/%m/%d} before:{before_date:%Y/%m/%d}"
        message_ids: list[str] = []
        page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "q": query,
                "maxResults": 100,
                "includeSpamTrash": False,
            }
            if page_token:
                params["pageToken"] = page_token

            response = self.client.get(
                f"{GMAIL_API_BASE_URL}/messages",
                headers=self._headers(access_token),
                params=params,
                timeout=10,
            )
            self._raise_for_response(response)
            payload = response.json()
            message_ids.extend(
                str(message["id"])
                for message in payload.get("messages", [])
                if message.get("id")
            )
            page_token = payload.get("nextPageToken")
            if not page_token:
                return message_ids

    def _modify_labels(
        self,
        access_token: str,
        message_id: str,
        *,
        payload: dict[str, list[str]],
    ) -> list[str]:
        response = self.client.post(
            f"{GMAIL_API_BASE_URL}/messages/{message_id}/modify",
            headers=self._headers(access_token),
            json=payload,
            timeout=10,
        )
        self._raise_for_response(response)
        return [str(label) for label in response.json().get("labelIds", [])]

    @staticmethod
    def _headers(access_token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {access_token}"}

    @staticmethod
    def _raise_for_response(response: Any, *, auth_operation: bool = False) -> None:
        status_code = int(getattr(response, "status_code", 500))
        if status_code < 400:
            return
        if status_code in {401, 403} or auth_operation:
            raise ProviderError(
                "MAILBOX_REAUTH_REQUIRED",
                "Gmail authorization is no longer valid.",
                401,
            )
        if status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", "Gmail rate limit exceeded.", 429)
        raise ProviderError("PROVIDER_SYNC_FAILED", "Gmail request failed.", 502)
