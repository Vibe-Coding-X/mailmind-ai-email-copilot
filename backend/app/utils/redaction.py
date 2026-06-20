from __future__ import annotations

import re
from collections.abc import Iterable


REDACTED = "[REDACTED]"
SENSITIVE_KEY_PARTS = frozenset(
    {
        "token",
        "authorization",
        "password",
        "secret",
        "api_key",
        "apikey",
        "cookie",
        "session",
        "body_text",
        "raw_payload",
        "mime",
    }
)

OPENAI_KEY_RE = re.compile(r"\bsk-[A-Za-z0-9_-]{6,}\b")
AUTHORIZATION_BEARER_RE = re.compile(
    r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;\"']+"
)
BARE_BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
COOKIE_RE = re.compile(r"(?i)(cookie\s*[:=]\s*)[^;\r\n]+")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)([\"']?\b"
    r"(?:access[_-]?token|refresh[_-]?token|api[_ -]?key|session(?:id)?|"
    r"password|secret)"
    r"\b[\"']?\s*[:=]\s*[\"']?)[^\"',;\s}]+"
)


def redact_text(value: object, *, extra_secrets: Iterable[str] = ()) -> str:
    redacted = "" if value is None else str(value)
    for secret in sorted((secret for secret in extra_secrets if secret), key=len, reverse=True):
        redacted = redacted.replace(secret, REDACTED)
    redacted = AUTHORIZATION_BEARER_RE.sub(r"\1" + REDACTED, redacted)
    redacted = BARE_BEARER_RE.sub("Bearer " + REDACTED, redacted)
    redacted = COOKIE_RE.sub(r"\1" + REDACTED, redacted)
    redacted = SECRET_ASSIGNMENT_RE.sub(r"\1" + REDACTED, redacted)
    return OPENAI_KEY_RE.sub(REDACTED, redacted)


def safe_error_message(
    message: object | None,
    *,
    max_length: int = 1000,
    extra_secrets: Iterable[str] = (),
) -> str | None:
    if message is None:
        return None
    return redact_text(message, extra_secrets=extra_secrets)[:max_length]


def sanitize_sensitive_data(value: object) -> object:
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        for key, nested_value in value.items():
            string_key = str(key)
            if is_sensitive_key(string_key):
                continue
            sanitized[string_key] = sanitize_sensitive_data(nested_value)
        return sanitized
    if isinstance(value, list):
        return [sanitize_sensitive_data(item) for item in value]
    if isinstance(value, str):
        return redact_text(value)
    return value


def is_sensitive_key(key: str) -> bool:
    lowered = key.lower().replace("-", "_")
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)
