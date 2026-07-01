from __future__ import annotations

import hashlib
import imaplib
import logging
import re
import socket
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email import policy
from email.message import EmailMessage, Message
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime, parseaddr
from html import unescape
from typing import Any, Callable

from app.providers.base import (
    ProviderArchiveBatch,
    ProviderCapabilities,
    ProviderEmailBody,
    ProviderEmailMessage,
    ProviderError,
)


ClientFactory = Callable[[str, int], Any]
logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ImapMailboxConfig:
    host: str
    port: int
    username: str
    folder: str = "INBOX"
    use_ssl: bool = True
    uidvalidity: str | None = None
    account_email: str | None = None
    mailbox_id: str | None = None


class ImapProvider:
    provider_key = "imap"

    def __init__(
        self,
        *,
        config: ImapMailboxConfig | None = None,
        client_factory: ClientFactory | None = None,
    ) -> None:
        self.config = config
        self.client_factory = client_factory

    def with_mailbox_config(self, config: ImapMailboxConfig) -> "ImapProvider":
        return ImapProvider(config=config, client_factory=self.client_factory)

    def get_capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
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

    def refresh_access_token(self, refresh_token: str) -> str:
        return refresh_token

    def check_connection(self, password: str) -> None:
        logger.info("IMAP connection check start %s", _log_mailbox_context(self._config))
        client = self._connect()
        try:
            self._login(client, password)
            self._select_folder(client)
        finally:
            _close_client(client)
        logger.info("IMAP connection check completed %s", _log_mailbox_context(self._config))

    def list_messages_for_window(
        self,
        access_token: str,
        *,
        window_start: datetime,
        window_end: datetime,
    ) -> list[ProviderEmailMessage]:
        logger.info(
            "IMAP sync start %s window_start=%s window_end=%s",
            _log_mailbox_context(self._config),
            window_start.isoformat(),
            window_end.isoformat(),
        )
        client = self._connect()
        try:
            self._login(client, access_token)
            uidvalidity = self._select_folder(client)
            message_uids = self._search_message_uids(client, window_start, window_end)
            logger.info(
                "IMAP search completed %s uid_count=%s uidvalidity=%s",
                _log_mailbox_context(self._config),
                len(message_uids),
                uidvalidity,
            )
            messages: list[ProviderEmailMessage] = []
            for uid in message_uids:
                logger.info("IMAP fetch start %s uid=%s", _log_mailbox_context(self._config), uid)
                try:
                    fetched = self._fetch_message(client, uid)
                    if fetched is None:
                        logger.info(
                            "IMAP fetch skipped %s uid=%s reason=no_message_payload",
                            _log_mailbox_context(self._config),
                            uid,
                        )
                        continue
                    raw_message, flags = fetched
                    messages.append(
                        _parse_imap_message(
                            raw_message,
                            flags=flags,
                            folder=self._config.folder,
                            uidvalidity=uidvalidity,
                            uid=uid,
                        )
                    )
                    logger.info(
                        "IMAP fetch completed %s uid=%s flags=%s",
                        _log_mailbox_context(self._config),
                        uid,
                        ",".join(flags) if flags else "-",
                    )
                except ProviderError as exc:
                    logger.warning(
                        "IMAP fetch failed; skipping message %s uid=%s code=%s message=%s",
                        _log_mailbox_context(self._config),
                        uid,
                        exc.code,
                        exc.message,
                    )
                    continue
                except Exception as exc:
                    logger.warning(
                        "IMAP parse failed; skipping message %s uid=%s error=%s",
                        _log_mailbox_context(self._config),
                        uid,
                        exc,
                    )
                    continue
            logger.info(
                "IMAP sync completed %s message_count=%s uidvalidity=%s",
                _log_mailbox_context(self._config),
                len(messages),
                uidvalidity,
            )
            return messages
        finally:
            _close_client(client)

    def list_archive_batch(
        self,
        access_token: str,
        *,
        cursor: dict[str, Any] | None,
        batch_size: int,
    ) -> ProviderArchiveBatch:
        logger.info(
            "IMAP archive batch start %s cursor=%s batch_size=%s",
            _log_mailbox_context(self._config),
            _safe_cursor(cursor),
            batch_size,
        )
        client = self._connect()
        try:
            self._login(client, access_token)
            uidvalidity = self._select_folder(client)
            message_uids = self._search_archive_uids(client, cursor=cursor)
            selected_uids = message_uids[: max(1, batch_size)]
            messages: list[ProviderEmailMessage] = []
            for uid in selected_uids:
                logger.info(
                    "IMAP archive fetch start %s uid=%s",
                    _log_mailbox_context(self._config),
                    uid,
                )
                try:
                    fetched = self._fetch_message(client, uid)
                    if fetched is None:
                        logger.info(
                            "IMAP archive fetch skipped %s uid=%s reason=no_message_payload",
                            _log_mailbox_context(self._config),
                            uid,
                        )
                        continue
                    raw_message, flags = fetched
                    messages.append(
                        _parse_imap_message(
                            raw_message,
                            flags=flags,
                            folder=self._config.folder,
                            uidvalidity=uidvalidity,
                            uid=uid,
                        )
                    )
                    logger.info(
                        "IMAP archive fetch completed %s uid=%s flags=%s",
                        _log_mailbox_context(self._config),
                        uid,
                        ",".join(flags) if flags else "-",
                    )
                except ProviderError as exc:
                    logger.warning(
                        "IMAP archive fetch failed; skipping message %s uid=%s code=%s message=%s",
                        _log_mailbox_context(self._config),
                        uid,
                        exc.code,
                        exc.message,
                    )
                    continue
                except Exception as exc:
                    logger.warning(
                        "IMAP archive parse failed; skipping message %s uid=%s error=%s",
                        _log_mailbox_context(self._config),
                        uid,
                        exc,
                    )
                    continue
            next_cursor = (
                {"before_uid": str(min(int(uid) for uid in selected_uids))}
                if selected_uids
                else None
            )
            logger.info(
                "IMAP archive batch completed %s searched_uid_count=%s fetched_count=%s next_cursor=%s",
                _log_mailbox_context(self._config),
                len(message_uids),
                len(messages),
                _safe_cursor(next_cursor),
            )
            return ProviderArchiveBatch(
                messages=messages,
                cursor=next_cursor,
                is_complete=not selected_uids,
            )
        finally:
            _close_client(client)

    def get_message_detail(
        self,
        access_token: str,
        message_id: str,
    ) -> ProviderEmailMessage:
        raise ProviderError("imap_operation_unsupported", "IMAP detail fetch is not supported.", 400)

    def get_message_body(self, access_token: str, message_id: str) -> ProviderEmailBody:
        folder, uidvalidity, uid = _parse_external_id(message_id)
        config = self._config
        if folder != config.folder or (
            config.uidvalidity is not None and uidvalidity != config.uidvalidity
        ):
            raise ProviderError(
                "imap_message_id_invalid",
                "IMAP message id does not match this mailbox folder.",
                400,
            )
        logger.info(
            "IMAP body fetch start %s uid=%s",
            _log_mailbox_context(config),
            uid,
        )
        client = self._connect()
        try:
            self._login(client, access_token)
            selected_uidvalidity = self._select_folder(client)
            if uidvalidity != "unknown" and selected_uidvalidity != "unknown" and uidvalidity != selected_uidvalidity:
                raise ProviderError(
                    "imap_message_id_invalid",
                    "IMAP message id is no longer valid for this folder.",
                    400,
                )
            fetched = self._fetch_message(client, uid)
            if fetched is None:
                raise ProviderError("imap_message_not_found", "IMAP message was not found.", 404)
            raw_message, _ = fetched
            body = _parse_imap_body(raw_message)
            logger.info(
                "IMAP body fetch completed %s uid=%s body_cached=%s",
                _log_mailbox_context(config),
                uid,
                bool(body.body_text or body.body_html),
            )
            return body
        finally:
            _close_client(client)

    def mark_as_read(self, access_token: str, message_id: str) -> list[str]:
        raise ProviderError("imap_operation_unsupported", "IMAP mark-read is not wired yet.", 400)

    def mark_as_unread(self, access_token: str, message_id: str) -> list[str]:
        raise ProviderError("imap_operation_unsupported", "IMAP mark-unread is not wired yet.", 400)

    @property
    def _config(self) -> ImapMailboxConfig:
        if self.config is None:
            raise ProviderError("imap_config_missing", "IMAP mailbox configuration is missing.", 400)
        return self.config

    def _connect(self) -> Any:
        config = self._config
        factory = self.client_factory
        if factory is None:
            factory = imaplib.IMAP4_SSL if config.use_ssl else imaplib.IMAP4
        try:
            logger.info("IMAP connect start %s", _log_mailbox_context(config))
            return factory(config.host, config.port)
        except socket.timeout as exc:
            raise ProviderError("network_timeout", "IMAP connection timed out.", 504) from exc
        except ssl.SSLError as exc:
            raise ProviderError("network_tls", "IMAP TLS connection failed.", 502) from exc
        except OSError as exc:
            raise ProviderError("imap_connection_failed", "IMAP connection failed.", 502) from exc
        finally:
            logger.info("IMAP connect finished %s", _log_mailbox_context(config))

    def _login(self, client: Any, password: str) -> None:
        try:
            logger.info("IMAP login start %s", _log_mailbox_context(self._config))
            status, _ = client.login(self._config.username, password)
        except imaplib.IMAP4.error as exc:
            raise ProviderError("MAILBOX_REAUTH_REQUIRED", "IMAP authentication failed.", 401) from exc
        except socket.timeout as exc:
            raise ProviderError("network_timeout", "IMAP login timed out.", 504) from exc
        if _status_failed(status):
            raise ProviderError("MAILBOX_REAUTH_REQUIRED", "IMAP authentication failed.", 401)
        logger.info("IMAP login succeeded %s", _log_mailbox_context(self._config))

    def _select_folder(self, client: Any) -> str:
        try:
            logger.info("IMAP folder select start %s", _log_mailbox_context(self._config))
            status, _ = client.select(self._config.folder, readonly=True)
        except imaplib.IMAP4.error as exc:
            raise ProviderError("imap_folder_unavailable", "IMAP folder is unavailable.", 400) from exc
        if _status_failed(status):
            raise ProviderError("imap_folder_unavailable", "IMAP folder is unavailable.", 400)
        uidvalidity = self._config.uidvalidity or _uidvalidity_from_client(client) or "unknown"
        logger.info(
            "IMAP folder selected %s uidvalidity=%s",
            _log_mailbox_context(self._config),
            uidvalidity,
        )
        return uidvalidity

    def _search_message_uids(
        self,
        client: Any,
        window_start: datetime,
        window_end: datetime,
    ) -> list[str]:
        since = _imap_date(window_start)
        before = _imap_date(window_end + timedelta(days=1))
        try:
            logger.info(
                'IMAP search start %s since="%s" before="%s"',
                _log_mailbox_context(self._config),
                since,
                before,
            )
            status, data = client.uid("SEARCH", None, f'(SINCE "{since}" BEFORE "{before}")')
        except socket.timeout as exc:
            raise ProviderError("network_timeout", "IMAP search timed out.", 504) from exc
        if _status_failed(status):
            raise ProviderError("imap_search_failed", "IMAP message search failed.", 502)
        if not data:
            return []
        raw = data[0] or b""
        if isinstance(raw, bytes):
            raw = raw.decode("ascii", errors="ignore")
        return [uid for uid in str(raw).split() if uid]

    def _fetch_message(self, client: Any, uid: str) -> tuple[bytes, list[str]] | None:
        try:
            status, data = client.uid("FETCH", uid, "(RFC822 FLAGS)")
        except imaplib.IMAP4.error as exc:
            raise ProviderError("imap_fetch_failed", "IMAP message fetch failed.", 502) from exc
        except socket.timeout as exc:
            raise ProviderError("network_timeout", "IMAP fetch timed out.", 504) from exc
        if _status_failed(status):
            raise ProviderError("imap_fetch_failed", "IMAP message fetch failed.", 502)
        for item in data or []:
            if not isinstance(item, tuple) or len(item) < 2:
                continue
            meta, raw_message = item[0], item[1]
            if isinstance(raw_message, bytes):
                return raw_message, _flags_from_fetch_meta(meta)
        return None

    def _search_archive_uids(
        self,
        client: Any,
        *,
        cursor: dict[str, Any] | None,
    ) -> list[str]:
        raw_before_uid = (cursor or {}).get("before_uid")
        before_uid: int | None = None
        if raw_before_uid is not None:
            try:
                before_uid = int(str(raw_before_uid))
            except ValueError:
                before_uid = None
        uid_range = "1:*" if before_uid is None else f"1:{max(0, before_uid - 1)}"
        try:
            logger.info(
                'IMAP archive search start %s uid_range="%s"',
                _log_mailbox_context(self._config),
                uid_range,
            )
            status, data = client.uid("SEARCH", None, f"UID {uid_range}")
        except socket.timeout as exc:
            raise ProviderError("network_timeout", "IMAP archive search timed out.", 504) from exc
        if _status_failed(status):
            raise ProviderError("imap_search_failed", "IMAP archive message search failed.", 502)
        if not data:
            return []
        raw = data[0] or b""
        if isinstance(raw, bytes):
            raw = raw.decode("ascii", errors="ignore")
        uids = [uid for uid in str(raw).split() if uid.isdigit()]
        return sorted(uids, key=lambda uid: int(uid), reverse=True)


def _parse_imap_message(
    raw_message: bytes,
    *,
    flags: list[str],
    folder: str,
    uidvalidity: str,
    uid: str,
) -> ProviderEmailMessage:
    parsed = BytesParser(policy=policy.default).parsebytes(raw_message)
    subject = _header_value(parsed, "subject")
    from_name, from_address = parseaddr(_header_value(parsed, "from") or "")
    body_text = _message_body(parsed)
    received_at = _message_received_at(parsed)
    return ProviderEmailMessage(
        external_id=f"{folder}:{uidvalidity}:{uid}",
        external_thread_id=None,
        internet_message_id=_header_value(parsed, "message-id"),
        subject=subject,
        from_name=from_name or None,
        from_address=from_address or None,
        to_addresses=_addresses(parsed, "to"),
        cc_addresses=_addresses(parsed, "cc"),
        snippet=(body_text or "")[:200] or None,
        body_text=(body_text or "")[:10000] or None,
        body_text_truncated=len(body_text or "") > 10000,
        received_at=received_at,
        is_read="\\Seen" in flags,
        provider_labels=flags,
        gmail_history_id=None,
        raw_payload_hash=hashlib.sha256(raw_message).hexdigest(),
    )


def _parse_imap_body(raw_message: bytes) -> ProviderEmailBody:
    parsed = BytesParser(policy=policy.default).parsebytes(raw_message)
    body_text = _message_body(parsed)
    body_html = _message_html(parsed)
    return ProviderEmailBody(
        body_text=(body_text or "")[:10000] or None,
        body_html=body_html,
        body_text_truncated=len(body_text or "") > 10000,
    )


def _message_body(message: Message) -> str | None:
    if isinstance(message, EmailMessage):
        plain = message.get_body(preferencelist=("plain",))
        if plain is not None:
            return _payload_text(plain)
        html = message.get_body(preferencelist=("html",))
        if html is not None:
            return _html_to_text(_payload_text(html) or "")
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain":
                return _payload_text(part)
    return _payload_text(message)


def _message_html(message: Message) -> str | None:
    if isinstance(message, EmailMessage):
        html = message.get_body(preferencelist=("html",))
        if html is not None:
            return _payload_text(html)
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/html":
                return _payload_text(part)
    if message.get_content_type() == "text/html":
        return _payload_text(message)
    return None


def _payload_text(message: Message) -> str | None:
    try:
        content = message.get_content()
    except Exception:
        payload = message.get_payload(decode=True)
        if isinstance(payload, bytes):
            return payload.decode(message.get_content_charset() or "utf-8", errors="replace")
        return str(payload or "") or None
    return str(content or "") or None


def _message_received_at(message: Message) -> datetime:
    value = _header_value(message, "date")
    if value:
        try:
            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except (TypeError, ValueError):
            pass
    return datetime.now(UTC)


def _addresses(message: Message, header: str) -> list[str]:
    values = message.get_all(header, [])
    return [address for _, address in getaddresses(values) if address]


def _header_value(message: Message, header: str) -> str | None:
    value = message.get(header)
    return str(value) if value else None


def _html_to_text(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def _flags_from_fetch_meta(meta: object) -> list[str]:
    if isinstance(meta, bytes):
        meta_text = meta.decode("ascii", errors="ignore")
    else:
        meta_text = str(meta)
    match = re.search(r"FLAGS \(([^)]*)\)", meta_text)
    if match is None:
        return []
    return [flag for flag in match.group(1).split() if flag]


def _uidvalidity_from_client(client: Any) -> str | None:
    response = getattr(client, "response", None)
    if not callable(response):
        return None
    try:
        _, data = response("UIDVALIDITY")
    except Exception:
        return None
    if not data:
        return None
    value = data[0]
    if isinstance(value, bytes):
        value = value.decode("ascii", errors="ignore")
    return str(value or "") or None


def _imap_date(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%d-%b-%Y")


def _parse_external_id(message_id: str) -> tuple[str, str, str]:
    parts = message_id.rsplit(":", 2)
    if len(parts) != 3 or not parts[0] or not parts[1] or not parts[2].isdigit():
        raise ProviderError(
            "imap_message_id_invalid",
            "IMAP message id is invalid.",
            400,
        )
    return parts[0], parts[1], parts[2]


def _status_failed(status: object) -> bool:
    return str(status).upper() != "OK"


def _close_client(client: Any) -> None:
    try:
        client.close()
    except Exception:
        pass
    try:
        client.logout()
    except Exception:
        pass


def _safe_cursor(cursor: dict[str, Any] | None) -> dict[str, str] | None:
    if not cursor:
        return None
    result: dict[str, str] = {}
    before_uid = cursor.get("before_uid")
    if before_uid is not None:
        result["before_uid"] = str(before_uid)
    return result or None


def _log_mailbox_context(config: ImapMailboxConfig) -> str:
    context = [
        f"host={config.host}",
        f"port={config.port}",
        f"username={config.username}",
        f"folder={config.folder}",
        f"ssl={config.use_ssl}",
    ]
    if config.account_email:
        context.append(f"account_email={config.account_email}")
    if config.mailbox_id:
        context.append(f"mailbox_id={config.mailbox_id}")
    return " ".join(context)
