from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.providers.gmail import GmailProvider


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


def test_refresh_access_token_exchanges_refresh_token() -> None:
    client = FakeHttpClient()
    provider = GmailProvider(client=client)

    access_token = provider.refresh_access_token("fake-refresh-token")

    assert access_token == "fake-access-token"
    assert client.post_calls[0]["data"]["grant_type"] == "refresh_token"
    assert client.post_calls[0]["data"]["refresh_token"] == "fake-refresh-token"


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
