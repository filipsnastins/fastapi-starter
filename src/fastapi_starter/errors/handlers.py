import structlog
from fastapi import Request
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

logger: structlog.stdlib.BoundLogger = structlog.get_logger()


async def log_http_error(request: Request, exc: HTTPException) -> JSONResponse:
    log = logger.bind(status_code=exc.status_code, detail=exc.detail)
    if exc.status_code in [401, 403, 404]:
        log.info("http_error")
    else:
        log.error("http_error")
    return await http_exception_handler(request, exc)


async def log_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    logger.info("request_validation_error", status_code=422, detail=exc.json())
    return await request_validation_exception_handler(request, exc)


async def log_unhandled_exception(_: Request, exc: RequestValidationError) -> None:
    logger.exception("unhandled_exception", status_code=500, exc_info=exc)
    raise exc from exc
