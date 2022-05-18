from __future__ import annotations

import logging
from functools import lru_cache
from typing import List, Optional

from pydantic import AnyHttpUrl, BaseSettings  # pylint: disable=no-name-in-module


@lru_cache
def get_settings() -> Settings:
    return Settings()


class Settings(BaseSettings):
    APP_TITLE: str = "FastAPI Starter"
    APP_DESCRIPTION: str = "FastAPI with sensible defaults."

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    ENVIRONMENT: str

    LOG_LEVEL: int = logging.INFO
    LOG_DEV: bool = False

    API_V1_STR: str = "/api/v1"

    ROOT_PATH: str = "/"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"

    HEALTHCHECK_ENDPOINT: str = "/api/v1/health/liveness"

    ALLOWED_HOSTS: List[str] = []
    CORS_ALLOW_ORIGINS: List[AnyHttpUrl] = []
    HTTPS_FORCE_REDIRECT: bool = False

    SQLALCHEMY_DATABASE_URI: str  # Secret
    SQLALCHEMY_POOL_SIZE: int = 10
    SQLALCHEMY_MAX_OVERFLOW: int = 0
    SQLALCHEMY_ECHO: bool = False

    SENTRY_DSN: Optional[str] = None  # Secret
    SENTRY_DEBUG: bool = False
    SENTRY_SAMPLE_RATE: float = 1.0
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1

    class Config:
        # Case sensitive set to false for secrets_dir to work
        case_sensitive = False
        # Docker secrets
        secrets_dir = "/run/secrets"
        # Synonyms
        fields = {
            "SQLALCHEMY_DATABASE_URI": {
                "env": [
                    "SQLALCHEMY_DATABASE_URI",
                    "DATABASE_URL",  # DigitalOcean
                ]
            }
        }

    # In order to use lru_cache, the class must be hashable
    def __hash__(self) -> int:
        return hash((type(self),) + tuple(str(getattr(self, f)) for f in self.__fields__.keys()))
