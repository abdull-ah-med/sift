"""Application settings from environment (``.env.example`` keys)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    sift_pg_dsn: str = Field(
        default="postgresql+asyncpg://sift:sift@127.0.0.1:5432/sift",
        alias="SIFT_PG_DSN",
    )
    sift_valkey_url: str = Field(
        default="redis://127.0.0.1:6379/0",
        alias="SIFT_VALKEY_URL",
    )
    sift_storage_endpoint: str = Field(
        default="http://127.0.0.1:8333",
        alias="SIFT_STORAGE_ENDPOINT",
    )
    sift_storage_bucket: str = Field(
        default="sift-uploads",
        alias="SIFT_STORAGE_BUCKET",
    )
    sift_api_key_pepper: str = Field(default="", alias="SIFT_API_KEY_PEPPER")
    sift_zitadel_issuer: str = Field(default="", alias="SIFT_ZITADEL_ISSUER")
    sift_zitadel_audience: str = Field(default="sift-api", alias="SIFT_ZITADEL_AUDIENCE")
    sift_storage_access_key: str = Field(default="sift", alias="SIFT_STORAGE_ACCESS_KEY")
    sift_storage_secret_key: str = Field(
        default="sift-dev-secret", alias="SIFT_STORAGE_SECRET_KEY"
    )
    sift_otlp_endpoint: str = Field(
        default="http://127.0.0.1:4318/v1/traces",
        alias="SIFT_OTLP_ENDPOINT",
    )
    sift_otel_enabled: bool = Field(default=False, alias="SIFT_OTEL_ENABLED")
    sift_tus_url: str = Field(
        default="http://127.0.0.1:1080/files/",
        alias="SIFT_TUS_URL",
    )
    sift_bootstrap_tenant_id: str = Field(default="", alias="SIFT_BOOTSTRAP_TENANT_ID")
    sift_zitadel_web_client_id: str = Field(default="", alias="SIFT_ZITADEL_WEB_CLIENT_ID")
    sift_zitadel_cli_client_id: str = Field(default="", alias="SIFT_ZITADEL_CLI_CLIENT_ID")


@lru_cache
def get_settings() -> Settings:
    return Settings()
