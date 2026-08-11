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


@lru_cache
def get_settings() -> Settings:
    return Settings()
