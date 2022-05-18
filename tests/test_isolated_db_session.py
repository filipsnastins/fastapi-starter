from typing import Any, Generator

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from fastapi_starter.db import get_db


# pylint: disable=unused-argument
@pytest.fixture(name="client")
def client_fixture(app: FastAPI, db: Session) -> Generator[TestClient, None, None]:
    @app.post("/_tests/test_isolated_db_session")
    def _create_table_route(db: Session = Depends(get_db)) -> Any:
        db.execute(text("CREATE table _tests_isolated_db_session (name VARCHAR(32))"))
        db.execute(text("INSERT INTO _tests_isolated_db_session (name) VALUES ('foo')"))
        db.commit()

    @app.get("/_tests/test_isolated_db_session")
    def _get_first_row_route(db: Session = Depends(get_db)) -> Any:
        row = db.execute(text("SELECT name FROM _tests_isolated_db_session")).first()
        if not row:
            return {"name": None}
        return {"name": row.name}

    with TestClient(app) as c:
        yield c


def test_table_created_by_calling_route(client: TestClient) -> None:
    client.post("/_tests/test_isolated_db_session")

    r = client.get("/_tests/test_isolated_db_session")
    data = r.json()

    assert data["name"] == "foo"


def test_table_does_not_exist_in_the_next_test_with_get_route(client: TestClient) -> None:
    with pytest.raises(OperationalError):
        client.get("/_tests/test_isolated_db_session")


def test_table_created_by_calling_db_fixture(db: Session) -> None:
    db.execute(text("CREATE table _tests_isolated_db_session (name VARCHAR(32))"))
    db.execute(text("INSERT INTO _tests_isolated_db_session (name) VALUES ('foo')"))
    db.commit()

    row = db.execute(text("SELECT name FROM _tests_isolated_db_session")).first()

    assert row is not None
    assert row.name == "foo"


def test_table_does_not_exist_in_the_next_test_with_db_fixture(db: Session) -> None:
    with pytest.raises(OperationalError):
        db.execute(text("SELECT name FROM _tests_isolated_db_session")).first()
