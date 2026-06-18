from app.core.config import Settings


def test_settings_can_be_constructed_with_development_defaults() -> None:
    settings = Settings()

    assert settings.app_env == "development"
    assert settings.app_host == "127.0.0.1"
    assert settings.app_port == 8000
    assert settings.default_timezone == "Asia/Shanghai"


def test_settings_reads_database_url_from_environment(monkeypatch) -> None:
    expected_url = "postgresql+psycopg://mailmind:mailmind@localhost:5432/mailmind"
    monkeypatch.setenv("DATABASE_URL", expected_url)

    settings = Settings()

    assert settings.database_url == expected_url


def test_secret_values_are_redacted_from_model_repr() -> None:
    settings = Settings(
        app_secret_key="test-secret",
        app_encryption_key="test-encryption-key",
        google_client_secret="test-google-secret",
        llm_api_key="test-llm-key",
    )

    rendered = repr(settings)

    assert "test-secret" not in rendered
    assert "test-encryption-key" not in rendered
    assert "test-google-secret" not in rendered
    assert "test-llm-key" not in rendered


def test_cors_allowed_origins_reads_comma_separated_environment(monkeypatch) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        "http://localhost:3000, http://127.0.0.1:3000",
    )

    settings = Settings()

    assert settings.cors_allowed_origins == [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
