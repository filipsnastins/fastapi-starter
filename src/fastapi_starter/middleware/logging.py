"""Logging Middleware

Configures global logging library like structlog
with sensible defaults and binds unique X-Request-ID to every incoming request.

Configuration of both should happen at the same time in correct order,
because logging expects to get request_id.

asgi-correlation-id library is used for request_id handling with default configuration.
If X-Request-ID is not present in request header, new unique request_id is generated.
X-Request-ID is returned in response headers.

Supported loggers:
- structlog via StructlogLoggingMiddlewareFactory

Globally binded keys to every log entry:
- method
- path
- remote_addr
- request_id
- scheme
"""
from __future__ import annotations

import logging
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Type

import structlog
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from structlog.contextvars import bind_contextvars, clear_contextvars, merge_contextvars


class SupportedLoggers(Enum):
    STRUCTLOG = "structlog"


class LoggingMiddleware:
    def __init__(
        self,
        app: FastAPI,
        factory: LoggingMiddlewareFactory,
        log_level: int = logging.INFO,
        timestamp_fmt: str = "iso",
        timestamp_utc: bool = False,
        dev: bool = True,
    ):
        self._app = app
        self._factory = factory
        self._log_level = log_level
        self._timestamp_fmt = timestamp_fmt
        self._timestamp_utc = timestamp_utc
        self._dev = dev

        self._configure_logging()
        self._add_logging_middleware()
        self._add_request_id_middleware()

    def _configure_logging(self) -> None:
        logging_configurator = self._factory.create_logging_configurator()
        logging_configurator.configure_logging(
            log_level=self._log_level,
            timestamp_fmt=self._timestamp_fmt,
            timestamp_utc=self._timestamp_utc,
            dev=self._dev,
        )

    def _add_logging_middleware(self) -> None:
        logging_middeware = self._factory.create_logging_middeware()
        self._app.add_middleware(logging_middeware)

    def _add_request_id_middleware(self) -> None:
        self._app.add_middleware(CorrelationIdMiddleware)


class LoggingMiddlewareFactory(ABC):
    @abstractmethod
    def create_logging_configurator(self) -> BaseLoggingConfigurator:
        pass

    @abstractmethod
    def create_logging_middeware(self) -> Type[BaseLoggingMiddleware]:
        pass


class BaseLoggingConfigurator(ABC):
    @abstractmethod
    def configure_logging(
        self,
        log_level: int,
        timestamp_fmt: str,
        timestamp_utc: bool,
        dev: bool,
    ) -> None:
        pass


class BaseLoggingMiddleware(ABC, BaseHTTPMiddleware):
    @abstractmethod
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        pass


class StructlogLoggingMiddlewareFactory(LoggingMiddlewareFactory):
    def create_logging_configurator(self) -> BaseLoggingConfigurator:
        return StructlogLoggingConfigurator()

    def create_logging_middeware(self) -> Type[BaseLoggingMiddleware]:
        return StructlogLoggingMiddleware


class StructlogLoggingConfigurator(BaseLoggingConfigurator):
    def configure_logging(
        self,
        log_level: int,
        timestamp_fmt: str,
        timestamp_utc: bool,
        dev: bool,
    ) -> None:
        processors = [
            merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt=timestamp_fmt, utc=timestamp_utc),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ]
        if dev:
            processors.append(structlog.processors.ExceptionPrettyPrinter())
            processors.append(structlog.dev.ConsoleRenderer())
        else:
            processors.append(structlog.processors.KeyValueRenderer(sort_keys=True))
        logging.basicConfig(format="%(message)s", stream=sys.stdout, level=log_level)
        structlog.configure(
            processors=processors,  # type: ignore
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )


class StructlogLoggingMiddleware(BaseLoggingMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        clear_contextvars()
        bind_contextvars(
            method=request.method,
            path=request.url.path,
            remote_addr=request.client and request.client.host,
            request_id=correlation_id.get(),
            scheme=request.url.scheme,
        )
        response = await call_next(request)
        return response
