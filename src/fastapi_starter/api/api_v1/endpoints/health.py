from typing import Any

import structlog
from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from .... import schemas
from ....db import get_db

router = APIRouter()
logger: structlog.stdlib.BoundLogger = structlog.get_logger()


@router.get("/liveness", response_model=schemas.Health)
def liveness() -> Any:
    """Check if application is able to process HTTP request."""
    return schemas.Health(healthy=True)


@router.get(
    "/readiness",
    response_model=schemas.Readiness,
    responses={
        503: {"model": schemas.Readiness},
    },
)
def readiness(response: Response, db: Session = Depends(get_db)) -> Any:
    """Return HTTP 503 if application is not ready to accept requests.

    Checks:
    - Application can connect to a database
    """
    try:
        row = db.execute(text("SELECT 1")).one()
        database_connection = row[0] == 1
    except SQLAlchemyError:
        database_connection = False
    checks = schemas.ReadinessChecks(database_connection=database_connection)
    ready = all(list(check[1] for check in checks))
    if not ready:
        response.status_code = 503
    result = {"ready": ready, "checks": checks}
    readiness_ = schemas.Readiness(**result)
    logger.info("readiness", **result)
    return readiness_
