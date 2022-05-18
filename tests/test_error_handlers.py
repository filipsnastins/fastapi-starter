from typing import Any

import pytest
import structlog
from _pytest.logging import LogCaptureFixture
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


@pytest.fixture(name="app", scope="module", autouse=True)
def app_fixture(app: FastAPI) -> FastAPI:
    @app.get("/_tests/_test_error_handlers/raise-http/{status_code}")
    def _raise_http_error(status_code: int) -> Any:
        raise HTTPException(status_code=status_code)

    @app.get("/_tests/_test_error_handlers/raise-request-validation-error")
    def _raise_request_validation_error(not_passed_param: str) -> Any:
        return not_passed_param

    @app.get("/_tests/_test_error_handlers/raise-unhandled-exception")
    def _raise_unhandled_exception() -> Any:
        raise ValueError("An error occurred")

    return app


@pytest.mark.parametrize(
    ("status_code", "error_message", "log_level"),
    [
        (401, "Unauthorized", "info"),
        (403, "Forbidden", "info"),
        (404, "Not Found", "info"),
        (405, "Method Not Allowed", "error"),
        (500, "Internal Server Error", "error"),
    ],
)
def test_http_error_handler(
    client: TestClient,
    caplog: LogCaptureFixture,
    status_code: int,
    error_message: str,
    log_level: str,
) -> None:
    r = client.get(f"/_tests/_test_error_handlers/raise-http/{status_code}")
    data = r.json()

    assert r.status_code == status_code
    assert data["detail"] == error_message
    assert "event='http_error'" in caplog.text
    assert f"status_code={status_code}" in caplog.text
    assert f"level='{log_level}'" in caplog.text


def test_validation_error_handled(client: TestClient, caplog: LogCaptureFixture) -> None:
    r = client.get("/_tests/_test_error_handlers/raise-request-validation-error")
    data = r.json()

    assert r.status_code == 422
    assert data["detail"][0]["loc"] == ["query", "not_passed_param"]
    assert data["detail"][0]["msg"] == "field required"
    assert data["detail"][0]["type"] == "value_error.missing"
    assert "event='request_validation_error'" in caplog.text
    assert "status_code=422" in caplog.text
    assert "level='info'" in caplog.text


def test_unhandled_exception_is_logged(client: TestClient, caplog: LogCaptureFixture) -> None:
    with pytest.raises(ValueError):
        client.get("/_tests/_test_error_handlers/raise-unhandled-exception")

    assert "ValueError: An error occurred" in caplog.text
    assert "event='unhandled_exception'" in caplog.text
    assert "status_code=500" in caplog.text
    assert "level='error'" in caplog.text
