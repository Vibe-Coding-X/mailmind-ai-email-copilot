from __future__ import annotations

from datetime import UTC, datetime

import pytest

from app.providers.base import ProviderCapabilities, ProviderError
from app.providers.outlook import OutlookProvider
from app.providers.registry import get_mailbox_provider


def test_outlook_provider_exposes_preparation_capabilities() -> None:
    provider = get_mailbox_provider("outlook")

    assert isinstance(provider, OutlookProvider)
    assert provider.provider_key == "outlook"
    assert provider.get_capabilities() == ProviderCapabilities(
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


def test_outlook_provider_operations_fail_with_controlled_error() -> None:
    provider = OutlookProvider()

    with pytest.raises(ProviderError) as exc_info:
        provider.list_messages_for_window(
            "fake-access-token",
            window_start=datetime(2026, 6, 23, 0, 0, tzinfo=UTC),
            window_end=datetime(2026, 6, 23, 12, 0, tzinfo=UTC),
        )

    assert exc_info.value.code == "outlook_not_configured"
    assert exc_info.value.status_code == 400
