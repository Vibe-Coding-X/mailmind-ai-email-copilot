from __future__ import annotations

import html
import re


MAX_BODY_TEXT_LENGTH = 20_000

_SCRIPT_STYLE_RE = re.compile(r"<(script|style)\b[^>]*>.*?</\1>", re.IGNORECASE | re.DOTALL)
_TAG_RE = re.compile(r"<[^>]+>")
_WHITESPACE_RE = re.compile(r"\s+")


def html_to_text(value: str) -> str:
    without_scripts = _SCRIPT_STYLE_RE.sub(" ", value)
    without_tags = _TAG_RE.sub(" ", without_scripts)
    return html.unescape(without_tags)


def clean_email_body(value: str | None, *, max_length: int = MAX_BODY_TEXT_LENGTH) -> tuple[str, bool]:
    if not value:
        return "", False

    without_nulls = value.replace("\x00", " ")
    cleaned = _WHITESPACE_RE.sub(" ", without_nulls).strip()
    if len(cleaned) <= max_length:
        return cleaned, False
    return cleaned[:max_length], True
