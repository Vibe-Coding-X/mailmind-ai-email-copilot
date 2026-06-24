from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx
import pytest

from app.providers.base import ProviderCapabilities, ProviderError
from app.providers.gmail import GmailProvider
from app.providers.registry import ProviderRegistryError, get_mailbox_provider


class FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> dict[str, Any]:
        return self._payload


class FakeHttpClient:
    def __init__(self) -> None:
        self.get_calls: list[dict[str, Any]] = []
        self.post_calls: list[dict[str, Any]] = []

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        timeout: int,
    ) -> FakeResponse:
        self.get_calls.append(
            {"url": url, "headers": headers, "params": params or {}, "timeout": timeout}
        )
        if url.endswith("/messages"):
            return FakeResponse(
                200,
                {"messages": [{"id": "inside"}, {"id": "outside"}]},
            )
        if url.endswith("/messages/inside"):
            return FakeResponse(
                200,
                {
                    "id": "inside",
                    "threadId": "thread-inside",
                    "labelIds": ["INBOX", "UNREAD"],
                    "internalDate": "1781834400000",
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Inside"},
                            {"name": "From", "value": "a@example.com"},
                        ],
                        "mimeType": "text/plain",
                        "body": {"data": "Qm9keQ"},
                    },
                },
            )
        return FakeResponse(
            200,
            {
                "id": "outside",
                "threadId": "thread-outside",
                "labelIds": ["INBOX"],
                "internalDate": "1781740800000",
                "payload": {
                    "headers": [{"name": "Subject", "value": "Outside"}],
                    "mimeType": "text/plain",
                    "body": {"data": "T2xk"},
                },
            },
        )

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: int,
    ) -> FakeResponse:
        self.post_calls.append(
            {
                "url": url,
                "headers": headers or {},
                "data": data or {},
                "json": json or {},
                "timeout": timeout,
            }
        )
        if url.endswith("/modify"):
            return FakeResponse(200, {"id": "message-id", "labelIds": ["INBOX"]})
        return FakeResponse(200, {"access_token": "fake-access-token", "expires_in": 3600})


class StaticHttpClient:
    def __init__(
        self,
        *,
        get_response: FakeResponse | None = None,
        post_response: FakeResponse | None = None,
    ) -> None:
        self.get_response = get_response or FakeResponse(200, {})
        self.post_response = post_response or FakeResponse(
            200, {"access_token": "fake-access-token", "expires_in": 3600}
        )

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        timeout: int,
    ) -> FakeResponse:
        return self.get_response

    def post(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        timeout: int,
    ) -> FakeResponse:
        return self.post_response


class PaginatedHttpClient:
    def __init__(self) -> None:
        self.get_calls: list[dict[str, Any]] = []

    def get(
        self,
        url: str,
        *,
        headers: dict[str, str],
        params: dict[str, Any] | None = None,
        timeout: int,
    ) -> FakeResponse:
        params = params or {}
        self.get_calls.append(
            {"url": url, "headers": headers, "params": params, "timeout": timeout}
        )
        if url.endswith("/messages"):
            if params.get("pageToken") == "next-page":
                return FakeResponse(
                    200,
                    {
                        "messages": [{"id": "page-1"}, {"id": "page-2"}],
                    },
                )
            return FakeResponse(
                200,
                {
                    "messages": [{"id": "page-1"}],
                    "nextPageToken": "next-page",
                },
            )

        message_id = url.rsplit("/", 1)[-1]
        return FakeResponse(
            200,
            {
                "id": message_id,
                "threadId": f"thread-{message_id}",
                "labelIds": ["INBOX"],
                "internalDate": "1781834400000",
                "payload": {
                    "headers": [{"name": "Subject", "value": message_id}],
                    "mimeType": "text/plain",
                    "body": {"data": "Qm9keQ"},
                },
            },
        )


class TimeoutHttpClient:
    def post(self, *args, **kwargs):
        raise httpx.TimeoutException("request timed out")

    def get(self, *args, **kwargs):
        raise httpx.TimeoutException("request timed out")


class TlsHttpClient:
    def post(self, *args, **kwargs):
        raise httpx.ConnectError("TLS handshake failed")

    def get(self, *args, **kwargs):
        raise httpx.ConnectError("TLS handshake failed")


def test_gmail_provider_exposes_capabilities() -> None:
    provider = GmailProvider(client=FakeHttpClient())

    assert provider.provider_key == "gmail"
    assert provider.get_capabilities() == ProviderCapabilities(
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


def test_provider_registry_returns_gmail_provider() -> None:
    provider = get_mailbox_provider("gmail")

    assert isinstance(provider, GmailProvider)
    assert provider.provider_key == "gmail"


def test_provider_registry_rejects_unsupported_provider() -> None:
    with pytest.raises(ProviderRegistryError) as exc_info:
        get_mailbox_provider("unknown")

    assert exc_info.value.code == "unsupported_mailbox_provider"
    assert exc_info.value.status_code == 400


def test_refresh_access_token_exchanges_refresh_token() -> None:
    client = FakeHttpClient()
    provider = GmailProvider(client=client)

    access_token = provider.refresh_access_token("fake-refresh-token")

    assert access_token == "fake-access-token"
    assert client.post_calls[0]["data"]["grant_type"] == "refresh_token"
    assert client.post_calls[0]["data"]["refresh_token"] == "fake-refresh-token"


def test_refresh_access_token_invalid_grant_requires_reauth() -> None:
    provider = GmailProvider(
        client=StaticHttpClient(
            post_response=FakeResponse(400, {"error": "invalid_grant"})
        )
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.refresh_access_token("fake-refresh-token")

    assert exc_info.value.code == "MAILBOX_REAUTH_REQUIRED"
    assert exc_info.value.message == "Gmail authorization is no longer valid."
    assert exc_info.value.status_code == 401


def test_gmail_api_access_not_configured_maps_to_provider_sync_failed() -> None:
    provider = GmailProvider(
        client=StaticHttpClient(
            get_response=FakeResponse(
                403,
                {
                    "error": {
                        "code": 403,
                        "message": (
                            "Gmail API has not been used in project 660896633151 "
                            "before or it is disabled."
                        ),
                        "status": "PERMISSION_DENIED",
                        "errors": [
                            {
                                "domain": "usageLimits",
                                "reason": "accessNotConfigured",
                                "message": "Access Not Configured.",
                            }
                        ],
                    }
                },
            )
        )
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.list_messages_for_window(
            "fake-access-token",
            window_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            window_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )

    assert exc_info.value.code == "PROVIDER_SYNC_FAILED"
    assert exc_info.value.message == "Gmail API is disabled for the Google Cloud project."
    assert exc_info.value.status_code == 502


def test_gmail_api_insufficient_scope_has_clear_permission_message() -> None:
    provider = GmailProvider(
        client=StaticHttpClient(
            get_response=FakeResponse(
                403,
                {
                    "error": {
                        "code": 403,
                        "message": "Request had insufficient authentication scopes.",
                        "status": "PERMISSION_DENIED",
                        "errors": [
                            {
                                "domain": "global",
                                "reason": "insufficientPermissions",
                                "message": "Insufficient Permission",
                            }
                        ],
                    }
                },
            )
        )
    )

    with pytest.raises(ProviderError) as exc_info:
        provider.list_messages_for_window(
            "fake-access-token",
            window_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            window_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )

    assert exc_info.value.code == "MAILBOX_REAUTH_REQUIRED"
    assert (
        exc_info.value.message
        == "Gmail authorization does not include the required Gmail scope."
    )
    assert exc_info.value.status_code == 401


def test_gmail_api_rate_limit_maps_to_provider_rate_limited() -> None:
    provider = GmailProvider(client=StaticHttpClient(get_response=FakeResponse(429, {})))

    with pytest.raises(ProviderError) as exc_info:
        provider.list_messages_for_window(
            "fake-access-token",
            window_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            window_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )

    assert exc_info.value.code == "PROVIDER_RATE_LIMITED"
    assert exc_info.value.message == "Gmail rate limit exceeded."


def test_gmail_timeout_maps_to_network_timeout() -> None:
    provider = GmailProvider(client=TimeoutHttpClient())

    with pytest.raises(ProviderError) as exc_info:
        provider.refresh_access_token("fake-refresh-token")

    assert exc_info.value.code == "network_timeout"
    assert exc_info.value.message == "Gmail request timed out."
    assert exc_info.value.status_code == 504


def test_gmail_tls_error_maps_to_network_tls() -> None:
    provider = GmailProvider(client=TlsHttpClient())

    with pytest.raises(ProviderError) as exc_info:
        provider.list_messages_for_window(
            "fake-access-token",
            window_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
            window_end=datetime(2026, 6, 19, 10, 0, tzinfo=UTC),
        )

    assert exc_info.value.code == "network_tls"
    assert exc_info.value.message == "Gmail network/TLS connection failed."
    assert exc_info.value.status_code == 502


def test_list_messages_for_window_uses_gmail_date_query_and_filters_candidates() -> None:
    client = FakeHttpClient()
    provider = GmailProvider(client=client)
    window_start = datetime(2026, 6, 18, 16, 0, tzinfo=UTC)
    window_end = datetime(2026, 6, 19, 12, 0, tzinfo=UTC)

    messages = provider.list_messages_for_window(
        "fake-access-token", window_start=window_start, window_end=window_end
    )

    assert [message.external_id for message in messages] == ["inside"]
    list_call = client.get_calls[0]
    assert list_call["params"]["q"] == "after:2026/06/18 before:2026/06/20"
    assert list_call["headers"]["Authorization"] == "Bearer fake-access-token"


def test_list_messages_for_window_paginates_and_deduplicates_message_ids() -> None:
    client = PaginatedHttpClient()
    provider = GmailProvider(client=client)

    messages = provider.list_messages_for_window(
        "fake-access-token",
        window_start=datetime(2026, 6, 18, 16, 0, tzinfo=UTC),
        window_end=datetime(2026, 6, 19, 12, 0, tzinfo=UTC),
    )

    assert [message.external_id for message in messages] == ["page-1", "page-2"]
    list_calls = [call for call in client.get_calls if call["url"].endswith("/messages")]
    detail_calls = [call for call in client.get_calls if not call["url"].endswith("/messages")]
    assert len(list_calls) == 2
    assert list_calls[1]["params"]["pageToken"] == "next-page"
    assert [call["url"].rsplit("/", 1)[-1] for call in detail_calls] == [
        "page-1",
        "page-2",
    ]


def test_get_message_detail_parses_gmail_message() -> None:
    client = FakeHttpClient()
    provider = GmailProvider(client=client)

    message = provider.get_message_detail("fake-access-token", "inside")

    assert message.external_id == "inside"
    assert message.subject == "Inside"
    assert message.is_read is False


def test_mark_as_read_removes_unread_label() -> None:
    client = FakeHttpClient()
    provider = GmailProvider(client=client)

    labels = provider.mark_as_read("fake-access-token", "message-id")

    assert labels == ["INBOX"]
    assert client.post_calls[0]["json"] == {"removeLabelIds": ["UNREAD"]}


def test_mark_as_unread_adds_unread_label() -> None:
    client = FakeHttpClient()
    provider = GmailProvider(client=client)

    provider.mark_as_unread("fake-access-token", "message-id")

    assert client.post_calls[0]["json"] == {"addLabelIds": ["UNREAD"]}
