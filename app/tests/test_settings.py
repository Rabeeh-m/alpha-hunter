from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config.settings import Environment, Settings, get_settings

REQUIRED_ENV = {
    "SECRET_KEY": "test-secret-key",
    "DATABASE_URL": "postgresql+asyncpg://user:pass@localhost:5432/alpha_hunter_test",
    "REDIS_URL": "redis://localhost:6379/0",
}


def test_settings_load_with_required_env(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    settings = Settings()
    assert settings.app_name == "Alpha Hunter"
    assert settings.environment == Environment.LOCAL


def test_settings_missing_required_field_raises(monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.setenv("DATABASE_URL", REQUIRED_ENV["DATABASE_URL"])
    monkeypatch.setenv("REDIS_URL", REQUIRED_ENV["REDIS_URL"])
    monkeypatch.chdir("/tmp")
    with pytest.raises(ValidationError):
        Settings()


def test_celery_urls_default_to_redis_url(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("CELERY_BROKER_URL", raising=False)
    monkeypatch.delenv("CELERY_RESULT_BACKEND", raising=False)
    settings = Settings()
    assert str(settings.celery_broker_url) == str(settings.redis_url)


def test_get_settings_is_cached(monkeypatch):
    for key, value in REQUIRED_ENV.items():
        monkeypatch.setenv(key, value)
    get_settings.cache_clear()
    assert get_settings() is get_settings()
