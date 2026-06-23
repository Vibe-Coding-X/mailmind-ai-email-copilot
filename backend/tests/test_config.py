from pathlib import Path

from app.core.config import BACKEND_DIR, Settings


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


def test_background_job_settings_default_to_redis_url() -> None:
    settings = Settings(redis_url="redis://localhost:6379/2")

    assert settings.background_jobs_enabled is True
    assert settings.background_jobs_eager is False
    assert settings.celery_broker_url == "redis://localhost:6379/2"
    assert settings.celery_result_backend == "redis://localhost:6379/2"


def test_background_job_settings_can_enable_eager_mode(monkeypatch) -> None:
    monkeypatch.setenv("BACKGROUND_JOBS_EAGER", "true")
    monkeypatch.setenv("CELERY_BROKER_URL", "redis://localhost:6379/3")
    monkeypatch.setenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/4")

    settings = Settings()

    assert settings.background_jobs_eager is True
    assert settings.celery_broker_url == "redis://localhost:6379/3"
    assert settings.celery_result_backend == "redis://localhost:6379/4"


def test_settings_default_env_files_are_backend_relative() -> None:
    env_files = Settings.model_config["env_file"]

    assert env_files == (
        BACKEND_DIR / ".env",
        BACKEND_DIR / ".env.local",
    )
    assert BACKEND_DIR == Path(__file__).resolve().parents[1]


def test_settings_reads_env_then_env_local_with_environment_precedence(
    tmp_path,
    monkeypatch,
) -> None:
    env_file = tmp_path / ".env"
    env_local_file = tmp_path / ".env.local"
    env_file.write_text(
        "GOOGLE_CLIENT_ID=from-env\n"
        "GOOGLE_REDIRECT_URI=http://localhost:8000/from-env\n",
        encoding="utf-8",
    )
    env_local_file.write_text(
        "GOOGLE_CLIENT_ID=from-env-local\n"
        "GOOGLE_CLIENT_SECRET=from-local-secret\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("GOOGLE_CLIENT_SECRET", raising=False)
    monkeypatch.delenv("GOOGLE_REDIRECT_URI", raising=False)
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "from-process-env")

    settings = Settings(_env_file=(env_file, env_local_file))

    assert settings.google_client_id == "from-process-env"
    assert settings.google_client_secret.get_secret_value() == "from-local-secret"
    assert settings.google_redirect_uri == "http://localhost:8000/from-env"
