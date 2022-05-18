from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine, Transaction
from sqlalchemy.event import listens_for as sa_listens_for
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from fastapi_starter import FastAPIStarterTemplate
from fastapi_starter.core.config import Settings, get_settings
from fastapi_starter.db import get_db


@pytest.fixture(name="monkeypatch_session", scope="session")
def monkeypatch_session_fixture() -> Generator[MonkeyPatch, None, None]:
    """Enable Pytest monkeypath to work with session scope.

    https://github.com/pytest-dev/pytest/issues/1872.
    """
    m = MonkeyPatch()
    yield m
    m.undo()


@pytest.fixture(name="set_test_config", scope="session")
def set_test_config_fixture(monkeypatch_session: MonkeyPatch) -> None:
    monkeypatch_session.setenv("ENVIRONMENT", "test")
    monkeypatch_session.setenv("SQLALCHEMY_DATABASE_URI", "sqlite://")
    monkeypatch_session.setenv("ALLOWED_HOSTS", '["*"]')
    monkeypatch_session.setenv("CORS_ALLOW_ORIGINS", "[]")


# pylint: disable=unused-argument
@pytest.fixture(name="settings", scope="session")
def settings_fixture(set_test_config: None) -> Settings:
    return get_settings()


@pytest.fixture(name="engine", scope="session")
def engine_fixture(settings: Settings) -> Engine:
    engine = create_engine(
        settings.SQLALCHEMY_DATABASE_URI,
        connect_args={"check_same_thread": False},  # SQLite config
        poolclass=StaticPool,
        future=True,
        # echo=True,  # For debugging
    )

    # https://gist.github.com/snorfalorpagus/c48770e7d1fcb9438830304c4cca24b9
    # Emit our own BEGIN
    @sa_listens_for(engine, "begin")
    def _do_begin(conn: Connection) -> None:
        conn.execute(text("BEGIN"))

    return engine


@pytest.fixture(name="session_factory", scope="session")
def session_factory_fixture(engine: Engine) -> sessionmaker:
    return sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        future=True,
    )


# pylint: disable=unused-argument
@pytest.fixture(name="app", scope="session")
def app_fixture(settings: Settings) -> FastAPI:
    return FastAPIStarterTemplate().create_app()


@pytest.fixture(name="db", scope="function", autouse=True)
def db_fixture(
    app: FastAPI, engine: Engine, session_factory: sessionmaker
) -> Generator[Session, None, None]:
    """Creates a new database session with working transaction for test duration."""
    connection = engine.connect()
    transaction = connection.begin()
    session = session_factory(bind=connection)
    nested = connection.begin_nested()

    # pylint: disable=unused-argument
    @sa_listens_for(session, "after_transaction_end")
    def _end_savepoint(session: Session, transaction: Transaction) -> None:
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    def _get_db() -> Session:
        return session

    app.dependency_overrides[get_db] = _get_db
    yield session
    app.dependency_overrides.clear()
    transaction.rollback()
    connection.close()


@pytest.fixture(name="client", scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
