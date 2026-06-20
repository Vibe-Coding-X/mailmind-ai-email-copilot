from app.utils.redaction import redact_text, safe_error_message, sanitize_sensitive_data


def test_redact_text_removes_common_secret_patterns() -> None:
    raw = (
        "Authorization: Bearer bearer-secret-12345 "
        "Cookie: sessionid=session-secret-12345; "
        "access_token=access-secret-12345 "
        "refresh_token=refresh-secret-12345 "
        "api_key=api-secret-12345 "
        "sk-testsecret123"
    )

    redacted = redact_text(raw)

    for secret in [
        "bearer-secret-12345",
        "session-secret-12345",
        "access-secret-12345",
        "refresh-secret-12345",
        "api-secret-12345",
        "sk-testsecret123",
    ]:
        assert secret not in redacted
    assert "[REDACTED]" in redacted


def test_sanitize_sensitive_data_drops_sensitive_keys_recursively() -> None:
    sanitized = sanitize_sensitive_data(
        {
            "subject": "Keep this",
            "nested": {
                "body_text": "Full private email body",
                "Cookie": "sessionid=session-secret-12345",
                "safe": "visible",
            },
            "items": [
                {"refresh_token": "refresh-secret-12345", "status": "ok"},
                {"authorization": "Bearer bearer-secret-12345", "count": 1},
            ],
        }
    )

    assert sanitized == {
        "subject": "Keep this",
        "nested": {"safe": "visible"},
        "items": [{"status": "ok"}, {"count": 1}],
    }


def test_safe_error_message_redacts_and_truncates() -> None:
    message = "Provider failed with api_key=api-secret-12345 " + ("x" * 100)

    redacted = safe_error_message(message, max_length=60)

    assert redacted is not None
    assert "api-secret-12345" not in redacted
    assert len(redacted) == 60
