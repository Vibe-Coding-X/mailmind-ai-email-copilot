from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import httpx

from app.core.config import Settings, get_settings
from app.providers.base import (
    ProviderArchiveBatch,
    ProviderCapabilities,
    ProviderEmailMessage,
    ProviderError,
)
from app.utils.email_parser import parse_gmail_message


GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GMAIL_API_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailProvider:
    provider_key = "gmail"

    def __init__(self, *, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self.client = client or httpx

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            can_mark_read=True,
            can_mark_unread=True,
            can_fetch_body=True,
            can_fetch_thread=True,
            can_archive=False,
            can_label=False,
            supports_oauth=True,
            supports_password_auth=False,
            supports_folders=False,
        )

    def refresh_access_token(self, refresh_token: str) -> str:
        try:
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
        except httpx.HTTPError as exc:
            raise _provider_error_from_httpx(exc) from exc
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

    def list_archive_batch(
        self,
        access_token: str,
        *,
        cursor: dict[str, Any] | None,
        batch_size: int,
    ) -> ProviderArchiveBatch:
        params: dict[str, Any] = {
            "maxResults": max(1, min(batch_size, 500)),
            "includeSpamTrash": False,
        }
        page_token = (cursor or {}).get("page_token")
        if page_token:
            params["pageToken"] = str(page_token)
        try:
            response = self.client.get(
                f"{GMAIL_API_BASE_URL}/messages",
                headers=self._headers(access_token),
                params=params,
                timeout=10,
            )
        except httpx.HTTPError as exc:
            raise _provider_error_from_httpx(exc) from exc
        self._raise_for_response(response)
        payload = response.json()
        message_ids = [
            str(message.get("id") or "")
            for message in payload.get("messages", [])
            if str(message.get("id") or "")
        ]
        messages = [
            self.get_message_detail(access_token, message_id)
            for message_id in message_ids
        ]
        next_page_token = payload.get("nextPageToken")
        return ProviderArchiveBatch(
            messages=messages,
            cursor={"page_token": str(next_page_token)} if next_page_token else None,
            is_complete=not bool(next_page_token),
        )

    def get_message_detail(self, access_token: str, message_id: str) -> ProviderEmailMessage:
        try:
            response = self.client.get(
                f"{GMAIL_API_BASE_URL}/messages/{message_id}",
                headers=self._headers(access_token),
                params={"format": "full"},
                timeout=10,
            )
        except httpx.HTTPError as exc:
            raise _provider_error_from_httpx(exc) from exc
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
        seen_message_ids: set[str] = set()
        page_token: str | None = None

        while True:
            params: dict[str, Any] = {
                "q": query,
                "maxResults": 100,
                "includeSpamTrash": False,
            }
            if page_token:
                params["pageToken"] = page_token

            try:
                response = self.client.get(
                    f"{GMAIL_API_BASE_URL}/messages",
                    headers=self._headers(access_token),
                    params=params,
                    timeout=10,
                )
            except httpx.HTTPError as exc:
                raise _provider_error_from_httpx(exc) from exc
            self._raise_for_response(response)
            payload = response.json()
            for message in payload.get("messages", []):
                message_id = str(message.get("id") or "")
                if not message_id or message_id in seen_message_ids:
                    continue
                seen_message_ids.add(message_id)
                message_ids.append(message_id)
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
        try:
            response = self.client.post(
                f"{GMAIL_API_BASE_URL}/messages/{message_id}/modify",
                headers=self._headers(access_token),
                json=payload,
                timeout=10,
            )
        except httpx.HTTPError as exc:
            raise _provider_error_from_httpx(exc) from exc
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
        if auth_operation:
            raise ProviderError(
                "MAILBOX_REAUTH_REQUIRED",
                "Gmail authorization is no longer valid.",
                401,
            )
        if status_code == 429:
            raise ProviderError("PROVIDER_RATE_LIMITED", "Gmail rate limit exceeded.", 429)
        if status_code == 401:
            raise ProviderError(
                "MAILBOX_REAUTH_REQUIRED",
                "Gmail authorization is no longer valid.",
                401,
            )
        if status_code == 403:
            error_details = _google_error_details(response)
            if error_details.is_api_disabled:
                raise ProviderError(
                    "PROVIDER_SYNC_FAILED",
                    "Gmail API is disabled for the Google Cloud project.",
                    502,
                )
            if error_details.is_scope_insufficient:
                raise ProviderError(
                    "MAILBOX_REAUTH_REQUIRED",
                    "Gmail authorization does not include the required Gmail scope.",
                    401,
                )
        raise ProviderError("PROVIDER_SYNC_FAILED", "Gmail request failed.", 502)


class _GoogleErrorDetails:
    def __init__(self, *, status: str, message: str, reasons: set[str]) -> None:
        self.status = status
        self.message = message
        self.reasons = reasons

    @property
    def is_api_disabled(self) -> bool:
        message = self.message.lower()
        return (
            "accessnotconfigured" in self.reasons
            or "gmail api has not been used" in message
            or "it is disabled" in message
        )

    @property
    def is_scope_insufficient(self) -> bool:
        status = self.status.lower()
        message = self.message.lower()
        return (
            "insufficientpermissions" in self.reasons
            or status == "access_token_scope_insufficient"
            or "access_token_scope_insufficient" in self.reasons
            or "insufficient authentication scopes" in message
            or "insufficient permission" in message
        )


def _google_error_details(response: Any) -> _GoogleErrorDetails:
    try:
        payload = response.json()
    except Exception:
        return _GoogleErrorDetails(status="", message="", reasons=set())
    if not isinstance(payload, dict):
        return _GoogleErrorDetails(status="", message="", reasons=set())

    error = payload.get("error")
    if isinstance(error, str):
        return _GoogleErrorDetails(status="", message=error, reasons={error.lower()})
    if not isinstance(error, dict):
        return _GoogleErrorDetails(status="", message="", reasons=set())

    status = str(error.get("status") or "")
    messages = [str(error.get("message") or "")]
    reasons: set[str] = set()
    errors = error.get("errors")
    if isinstance(errors, list):
        for item in errors:
            if not isinstance(item, dict):
                continue
            reason = str(item.get("reason") or "")
            message = str(item.get("message") or "")
            if reason:
                reasons.add(reason.lower())
            if message:
                messages.append(message)
    return _GoogleErrorDetails(
        status=status,
        message=" ".join(message for message in messages if message),
        reasons=reasons,
    )


def _provider_error_from_httpx(error: httpx.HTTPError) -> ProviderError:
    if isinstance(error, httpx.TimeoutException):
        return ProviderError("network_timeout", "Gmail request timed out.", 504)
    message = str(error).lower()
    if "tls" in message or "ssl" in message or "certificate" in message:
        return ProviderError(
            "network_tls",
            "Gmail network/TLS connection failed.",
            502,
        )
    return ProviderError("gmail_api_error", "Gmail request failed.", 502)
