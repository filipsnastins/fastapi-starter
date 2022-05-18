import sentry_sdk
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.httpsredirect import HTTPSRedirectMiddleware

from .api.api_v1.api import api_router as api_v1_router
from .core.config import Settings, get_settings
from .errors import log_http_error, log_unhandled_exception, log_validation_error
from .middleware import LoggingMiddleware, StructlogLoggingMiddlewareFactory


class FastAPIStarterTemplate:
    app: FastAPI
    settings: Settings

    def __init__(self) -> None:
        self.settings = self.init_settings()
        self.app = self.init_app(self.settings)

    def create_app(self) -> FastAPI:
        self.configure_logging()
        self.configure_error_handlers()
        self.configure_default_routes()
        self.configure_middleware()
        self.configure_sentry()
        return self.app

    def init_settings(self) -> Settings:
        return get_settings()

    def init_app(self, settings: Settings) -> FastAPI:
        return FastAPI(
            title=settings.APP_TITLE,
            description=settings.APP_DESCRIPTION,
            root_path=settings.ROOT_PATH,
            openapi_url=settings.OPENAPI_URL,
            docs_url=settings.DOCS_URL,
            redoc_url=settings.REDOC_URL,
        )

    def configure_logging(self) -> None:
        LoggingMiddleware(
            self.app,
            factory=StructlogLoggingMiddlewareFactory(),
            log_level=self.settings.LOG_LEVEL,
            dev=self.settings.LOG_DEV,
        )

    def configure_error_handlers(self) -> None:
        self.app.add_exception_handler(StarletteHTTPException, log_http_error)
        self.app.add_exception_handler(RequestValidationError, log_validation_error)
        self.app.add_exception_handler(Exception, log_unhandled_exception)

    def configure_default_routes(self) -> None:
        self.app.include_router(api_v1_router, prefix=self.settings.API_V1_STR)

    def configure_middleware(self) -> None:
        if self.settings.ALLOWED_HOSTS:
            self.app.add_middleware(
                TrustedHostMiddleware,
                allowed_hosts=[str(host) for host in self.settings.ALLOWED_HOSTS],
            )
        if self.settings.CORS_ALLOW_ORIGINS:
            self.app.add_middleware(
                CORSMiddleware,
                allow_origins=[str(origin) for origin in self.settings.CORS_ALLOW_ORIGINS],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
        if self.settings.HTTPS_FORCE_REDIRECT:
            self.app.add_middleware(HTTPSRedirectMiddleware)

    def configure_sentry(self) -> None:
        if self.settings.SENTRY_DSN:
            SentryAsgiMiddleware(self.app)
            # pylint: disable=abstract-class-instantiated
            sentry_sdk.init(
                dsn=self.settings.SENTRY_DSN,
                environment=self.settings.ENVIRONMENT,
                debug=self.settings.SENTRY_DEBUG,
                sample_rate=self.settings.SENTRY_SAMPLE_RATE,
                traces_sample_rate=self.settings.SENTRY_TRACES_SAMPLE_RATE,
            )
