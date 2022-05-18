import uuid
from typing import Any

import pytest
import structlog
from _pytest.logging import LogCaptureFixture
from fastapi import FastAPI
from fastapi.testclient import TestClient

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


@pytest.fixture(name="app", scope="module", autouse=True)
def app_fixture(app: FastAPI) -> FastAPI:
    @app.get("/_tests/_test_logging_middleware")
    def _test_logging_middleware_route() -> Any:
        logger.info("test_route")
        return {"message": "test_route"}

    return app


def test_request_id_returned_in_response_headers(client: TestClient) -> None:
    r = client.get("/_tests/_test_logging_middleware")

    assert r.headers.get("x-request-id")


def test_current_request_id_is_picked_up_from_headers(client: TestClient) -> None:
    request_id = uuid.uuid4().hex

    r = client.get("/_tests/_test_logging_middleware", headers={"X-Request-ID": request_id})

    assert request_id == r.headers.get("x-request-id")


def test_request_id_added_to_logs(client: TestClient, caplog: LogCaptureFixture) -> None:
    request_id = uuid.uuid4().hex

    client.get("/_tests/_test_logging_middleware", headers={"X-Request-ID": request_id})

    assert f"request_id='{request_id}'" in caplog.text
