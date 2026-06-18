from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000

    app_secret_key: SecretStr = Field(default=SecretStr("change-me"), repr=False)
    app_encryption_key: SecretStr = Field(
        default=SecretStr("change-me-32-byte-base64"), repr=False
    )
    app_encryption_key_version: str = "v1"

    database_url: str = "postgresql+psycopg://mailmind:mailmind@localhost:5432/mailmind"
    redis_url: str = "redis://localhost:6379/0"

    google_client_id: str = ""
    google_client_secret: SecretStr = Field(default=SecretStr(""), repr=False)
    google_redirect_uri: str = "http://localhost:8000/api/auth/gmail/callback"

    llm_provider: str = ""
    llm_api_key: SecretStr = Field(default=SecretStr(""), repr=False)
    llm_model: str = ""

    default_timezone: str = "Asia/Shanghai"

    digest_auto_generate: bool = True
    digest_generate_time: str = "08:00"

    model_config = SettingsConfigDict(
        env_file=None,
        env_prefix="",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_log_level(settings: Settings) -> Literal["DEBUG", "INFO"]:
    return "DEBUG" if settings.app_env == "development" else "INFO"
