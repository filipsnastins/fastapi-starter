from http import client as http_client
from http.client import HTTPConnection
from typing import Generator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from fastapi_starter.core.config import Settings
from fastapi_starter.db import get_db
from fastapi_starter.health.healthcheck import run_healthcheck


class HTTPResponse:
    status: int

    def read(self) -> bytes:
        return b'{"healthy": true}'


class MockHTTPConnection(HTTPConnection):
    def request(self, *args, **kwargs) -> None:  # type: ignore
        pass

    def getresponse(self) -> HTTPResponse:  # type: ignore
        return HTTPResponse()

    def close(self) -> None:
        pass


def test_passed_healthcheck_exits_0(monkeypatch: MonkeyPatch) -> None:
    HTTPResponse.status = 200
    monkeypatch.setattr(http_client, "HTTPConnection", MockHTTPConnection)

    with pytest.raises(SystemExit) as exc:
        run_healthcheck()

    assert exc.value.code == 0


def test_failed_healthcheck_exits_1(monkeypatch: MonkeyPatch) -> None:
    HTTPResponse.status = 500
    monkeypatch.setattr(http_client, "HTTPConnection", MockHTTPConnection)

    with pytest.raises(SystemExit) as exc:
        run_healthcheck()

    assert exc.value.code == 1


@pytest.fixture(name="set_get_db_to_invalid_database")
def set_get_db_to_invalid_database_fixture(app: FastAPI) -> Generator:
    def _get_db() -> Session:
        engine = create_engine("postgresql://user:password@foo:5432/app")
        session_factory = sessionmaker(engine)
        return session_factory()

    app.dependency_overrides[get_db] = _get_db
    yield
    app.dependency_overrides.clear()


def test_liveness_returns_200(client: TestClient, settings: Settings) -> None:
    r = client.get(f"{settings.API_V1_STR}/health/liveness")
    data = r.json()

    assert r.status_code == 200
    assert data["healthy"] is True


def test_readiness_returns_200(client: TestClient, settings: Settings) -> None:
    r = client.get(f"{settings.API_V1_STR}/health/readiness")
    data = r.json()

    assert r.status_code == 200
    assert data["ready"] is True


# pylint: disable=unused-argument
def test_readiness_returns_503_when_cannot_connect_to_a_database(
    client: TestClient, settings: Settings, set_get_db_to_invalid_database: None
) -> None:
    r = client.get(f"{settings.API_V1_STR}/health/readiness")
    data = r.json()

    assert r.status_code == 503
    assert data["ready"] is False
