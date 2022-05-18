from functools import lru_cache
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import get_settings


@lru_cache
def _create_engine() -> Engine:
    settings = get_settings()
    return create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        pool_size=settings.SQLALCHEMY_POOL_SIZE,
        max_overflow=settings.SQLALCHEMY_MAX_OVERFLOW,
        pool_pre_ping=True,
        future=True,
        echo=settings.SQLALCHEMY_ECHO,
    )


@lru_cache
def _create_session_factory() -> sessionmaker:
    engine = _create_engine()
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )


def get_db() -> Generator[Session, None, None]:
    session_factory = _create_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
