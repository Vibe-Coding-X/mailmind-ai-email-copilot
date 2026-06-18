import logging

from app.core.config import get_log_level, get_settings


SENSITIVE_FIELD_NAMES = frozenset(
    {
        "app_secret_key",
        "app_encryption_key",
        "google_client_secret",
        "llm_api_key",
    }
)


def configure_logging() -> None:
    settings = get_settings()
    logging.basicConfig(
        level=get_log_level(settings),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
