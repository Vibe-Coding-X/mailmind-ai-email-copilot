from __future__ import annotations

import imaplib
import socket
import ssl
from datetime import UTC, datetime

import pytest

from app.providers.base import ProviderCapabilities, ProviderError
from app.providers.imap import ImapMailboxConfig, ImapProvider
from app.providers.registry import get_mailbox_provider


RAW_MESSAGE = (
    b"Message-ID: <imap-message@example.com>\r\n"
    b"Date: Tue, 23 Jun 2026 03:04:05 +0000\r\n"
    b"Subject: IMAP subject\r\n"
    b"From: Sender Name <sender@example.com>\r\n"
    b"To: Inbox User <inbox@example.com>\r\n"
    b"Cc: Copy User <copy@example.com>\r\n"
    b"Content-Type: text/plain; charset=utf-8\r\n"
    b"\r\n"
    b"Hello from IMAP."
)


class FakeImapClient:
    def __init__(self, host: str, port: int) -> None:
        self.host = host
        self.port = port
        self.login_call: tuple[str, str] | None = None
        self.selected_folder: str | None = None
        self.uid_calls: list[tuple[object, ...]] = []
        self.closed = False
        self.logged_out = False

    def login(self, username: str, password: str):
        self.login_call = (username, password)
        return "OK", [b"logged in"]

    def select(self, folder: str, readonly: bool = False):
        self.selected_folder = folder
        assert readonly is True
        return "OK", [b"1"]

    def response(self, key: str):
        assert key == "UIDVALIDITY"
        return "OK", [b"999"]

    def uid(self, *args):
        self.uid_calls.append(args)
        if args[0] == "SEARCH":
            return "OK", [b"101"]
        if args[0] == "FETCH":
            return "OK", [(b"101 (FLAGS (\\Seen))", RAW_MESSAGE)]
        raise AssertionError(args)

    def close(self):
        self.closed = True

    def logout(self):
        self.logged_out = True


class PartialFailureImapClient(FakeImapClient):
    def uid(self, *args):
        self.uid_calls.append(args)
        if args[0] == "SEARCH":
            return "OK", [b"101 102"]
        if args[0] == "FETCH" and args[1] == "101":
            return "OK", [(b"101 (FLAGS (\\Seen))", RAW_MESSAGE)]
        if args[0] == "FETCH" and args[1] == "102":
            raise imaplib.IMAP4.error("fetch failed")
        raise AssertionError(args)


class ArchiveUidImapClient(FakeImapClient):
    def __init__(self, host: str, port: int, *, uids: bytes = b"101 102 103 104") -> None:
        super().__init__(host, port)
        self.uids = uids

    def uid(self, *args):
        self.uid_calls.append(args)
        if args[0] == "SEARCH":
            return "OK", [self.uids]
        if args[0] == "FETCH":
            uid = str(args[1])
            return "OK", [(f"{uid} (FLAGS (\\Seen))".encode("ascii"), RAW_MESSAGE)]
        raise AssertionError(args)


def _provider(client: FakeImapClient) -> ImapProvider:
    return ImapProvider(
        config=ImapMailboxConfig(
            host="imap.example.com",
            port=993,
            username="inbox@example.com",
            folder="Archive",
            use_ssl=True,
            account_email="account@example.com",
            mailbox_id="mailbox-123",
        ),
        client_factory=lambda host, port: client,
    )


def test_imap_provider_exposes_capabilities_and_registry_lookup() -> None:
    provider = get_mailbox_provider("imap")

    assert isinstance(provider, ImapProvider)
    assert provider.provider_key == "imap"
    assert provider.get_capabilities() == ProviderCapabilities(
        can_mark_read=True,
        can_mark_unread=True,
        can_fetch_body=True,
        can_fetch_thread=False,
        can_archive=False,
        can_label=False,
        supports_oauth=False,
        supports_password_auth=True,
        supports_folders=True,
    )


def test_imap_provider_lists_messages_with_contract_external_id() -> None:
    client = FakeImapClient("imap.example.com", 993)
    provider = _provider(client)

    messages = provider.list_messages_for_window(
        "fake-imap-password",
        window_start=datetime(2026, 6, 23, 0, 0, tzinfo=UTC),
        window_end=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
    )

    assert client.login_call == ("inbox@example.com", "fake-imap-password")
    assert client.selected_folder == "Archive"
    assert client.closed is True
    assert client.logged_out is True
    assert messages[0].external_id == "Archive:999:101"
    assert messages[0].external_thread_id is None
    assert messages[0].internet_message_id == "<imap-message@example.com>"
    assert messages[0].subject == "IMAP subject"
    assert messages[0].from_name == "Sender Name"
    assert messages[0].from_address == "sender@example.com"
    assert messages[0].to_addresses == ["inbox@example.com"]
    assert messages[0].cc_addresses == ["copy@example.com"]
    assert messages[0].body_text == "Hello from IMAP."
    assert messages[0].received_at == datetime(2026, 6, 23, 3, 4, 5, tzinfo=UTC)
    assert messages[0].is_read is True
    assert messages[0].provider_labels == ["\\Seen"]
    assert len(messages[0].raw_payload_hash) == 64


def test_imap_provider_get_message_body_fetches_uid_from_external_id() -> None:
    client = FakeImapClient("imap.example.com", 993)
    provider = _provider(client)

    body = provider.get_message_body("fake-imap-password", "Archive:999:101")

    assert body.body_text == "Hello from IMAP."
    assert body.body_html is None
    assert body.body_text_truncated is False
    fetch_call = [call for call in client.uid_calls if call[0] == "FETCH"][0]
    assert fetch_call[1] == "101"


def test_imap_provider_get_message_body_rejects_invalid_external_id() -> None:
    client = FakeImapClient("imap.example.com", 993)
    provider = _provider(client)

    with pytest.raises(ProviderError) as exc_info:
        provider.get_message_body("fake-imap-password", "bad-id")

    assert exc_info.value.code == "imap_message_id_invalid"
    assert exc_info.value.status_code == 400


def test_imap_provider_emits_step_logs(monkeypatch) -> None:
    client = FakeImapClient("imap.example.com", 993)
    provider = _provider(client)
    messages: list[str] = []

    def fake_info(message: str, *args) -> None:
        messages.append(message % args if args else message)

    monkeypatch.setattr("app.providers.imap.logger.info", fake_info)

    provider.list_messages_for_window(
        "fake-imap-password",
        window_start=datetime(2026, 6, 23, 0, 0, tzinfo=UTC),
        window_end=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
    )

    assert any("IMAP connect start" in message for message in messages)
    assert any("IMAP login succeeded" in message for message in messages)
    assert any("IMAP folder selected" in message for message in messages)
    assert any("IMAP search completed" in message for message in messages)
    assert any("IMAP fetch completed" in message for message in messages)
    assert any("IMAP sync completed" in message for message in messages)
    assert any("mailbox_id=mailbox-123" in message for message in messages)
    assert any("account_email=account@example.com" in message for message in messages)


def test_imap_provider_skips_single_message_fetch_failure(monkeypatch) -> None:
    client = PartialFailureImapClient("imap.example.com", 993)
    provider = _provider(client)
    warnings: list[str] = []

    def fake_warning(message: str, *args) -> None:
        warnings.append(message % args if args else message)

    monkeypatch.setattr("app.providers.imap.logger.warning", fake_warning)

    messages = provider.list_messages_for_window(
        "fake-imap-password",
        window_start=datetime(2026, 6, 23, 0, 0, tzinfo=UTC),
        window_end=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
    )

    assert [message.external_id for message in messages] == ["Archive:999:101"]
    assert any("IMAP fetch failed; skipping message" in message for message in warnings)
    assert any("uid=102" in message for message in warnings)


def test_imap_archive_batch_uses_uid_cursor_from_newer_to_older() -> None:
    client = ArchiveUidImapClient("imap.example.com", 993, uids=b"101 102 103 104")
    provider = _provider(client)

    batch = provider.list_archive_batch(
        "fake-imap-password",
        cursor=None,
        batch_size=2,
    )

    assert [message.external_id for message in batch.messages] == [
        "Archive:999:104",
        "Archive:999:103",
    ]
    assert batch.cursor == {"before_uid": "103"}
    assert batch.is_complete is False
    search_call = [call for call in client.uid_calls if call[0] == "SEARCH"][0]
    assert search_call == ("SEARCH", None, "UID 1:*")


def test_imap_archive_batch_continues_before_cursor_uid() -> None:
    client = ArchiveUidImapClient("imap.example.com", 993, uids=b"101 102")
    provider = _provider(client)

    batch = provider.list_archive_batch(
        "fake-imap-password",
        cursor={"before_uid": "103"},
        batch_size=2,
    )

    assert [message.external_id for message in batch.messages] == [
        "Archive:999:102",
        "Archive:999:101",
    ]
    assert batch.cursor == {"before_uid": "101"}
    assert batch.is_complete is False
    search_call = [call for call in client.uid_calls if call[0] == "SEARCH"][0]
    assert search_call == ("SEARCH", None, "UID 1:102")


def test_imap_archive_batch_marks_complete_when_no_older_uids() -> None:
    client = ArchiveUidImapClient("imap.example.com", 993, uids=b"")
    provider = _provider(client)

    batch = provider.list_archive_batch(
        "fake-imap-password",
        cursor={"before_uid": "101"},
        batch_size=2,
    )

    assert batch.messages == []
    assert batch.cursor is None
    assert batch.is_complete is True


def test_imap_provider_maps_authentication_failure_to_reauth() -> None:
    class AuthFailClient(FakeImapClient):
        def login(self, username: str, password: str):
            raise imaplib.IMAP4.error("authentication failed")

    with pytest.raises(ProviderError) as exc_info:
        _provider(AuthFailClient("imap.example.com", 993)).check_connection("bad-password")

    assert exc_info.value.code == "MAILBOX_REAUTH_REQUIRED"
    assert exc_info.value.status_code == 401


def test_imap_provider_maps_timeout_and_tls_failures() -> None:
    config = ImapMailboxConfig(host="imap.example.com", port=993, username="user")

    timeout_provider = ImapProvider(
        config=config,
        client_factory=lambda host, port: (_ for _ in ()).throw(socket.timeout()),
    )
    tls_provider = ImapProvider(
        config=config,
        client_factory=lambda host, port: (_ for _ in ()).throw(ssl.SSLError("tls")),
    )

    with pytest.raises(ProviderError) as timeout_error:
        timeout_provider.check_connection("password")
    with pytest.raises(ProviderError) as tls_error:
        tls_provider.check_connection("password")

    assert timeout_error.value.code == "network_timeout"
    assert tls_error.value.code == "network_tls"
