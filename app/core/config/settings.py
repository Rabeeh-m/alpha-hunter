from __future__ import annotations

from enum import StrEnum
from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    app_name: str = "Alpha Hunter"
    environment: Environment = Environment.LOCAL
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_json: bool = True

    secret_key: SecretStr = Field(..., description="Used to sign JWTs. Must be set.")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    database_url: PostgresDsn = Field(..., description="Async SQLAlchemy connection string")
    database_pool_size: int = 10
    database_max_overflow: int = 20
    database_echo: bool = False

    etherscan_api_key: SecretStr | None = Field(default=None, description="Etherscan API key for wallet scanning")
    redis_url: RedisDsn = Field(..., description="Used for caching and rate limiting")
    celery_broker_url: RedisDsn | None = None
    celery_result_backend: RedisDsn | None = None

    @field_validator("celery_broker_url", mode="before")
    @classmethod
    def default_celery_broker_to_redis(cls, v, info):
        return v or info.data.get("redis_url")

    @field_validator("celery_result_backend", mode="before")
    @classmethod
    def default_celery_backend_to_redis(cls, v, info):
        return v or info.data.get("redis_url")

    @property
    def is_production(self) -> bool:
        return self.environment == Environment.PRODUCTION

    github_token: SecretStr | None = None

@lru_cache
def get_settings() -> Settings:
    return Settings()
