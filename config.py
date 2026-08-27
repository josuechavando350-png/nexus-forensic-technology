from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    REDIS_URL: str
    JWT_SECRET_KEY: str
    LOG_FILE_PATH: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator(
        "NEO4J_URI",
        "NEO4J_USER",
        "NEO4J_PASSWORD",
        "REDIS_URL",
        "JWT_SECRET_KEY",
        "LOG_FILE_PATH",
    )
    @classmethod
    def _require_nonblank(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("configuration values must not be blank")
        return normalized

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def _validate_jwt_secret(cls, value: str) -> str:
        if len(value.encode("utf-8")) < 32:
            raise ValueError("JWT_SECRET_KEY must contain at least 32 bytes")
        return value

    @field_validator("NEO4J_URI")
    @classmethod
    def _validate_neo4j_uri(cls, value: str) -> str:
        if not value.startswith(("bolt://", "neo4j://", "neo4j+s://", "neo4j+ssc://")):
            raise ValueError("NEO4J_URI must use a supported Neo4j URI scheme")
        return value

    @field_validator("REDIS_URL")
    @classmethod
    def _validate_redis_url(cls, value: str) -> str:
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must use redis:// or rediss://")
        return value


# BaseSettings resolves required fields from the environment at runtime. Static mypy
# cannot infer that dynamic constructor behavior from pydantic-settings.
settings = Settings()  # type: ignore[call-arg]
