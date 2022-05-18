# fastapi-starter

[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

Quickly bootstrap pre-configured production grade FastAPI application.

FastAPI version corresponds to `fastapi_starter` package version.

This FastAPI project template is based on original [tiangolo/full-stack-fastapi-postgresql](https://github.com/tiangolo/full-stack-fastapi-postgresql)

- [fastapi-starter](#fastapi-starter)
  - [Features](#features)
  - [Usage Example](#usage-example)
  - [Configuration](#configuration)
  - [Installation](#installation)
  - [Development and testing](#development-and-testing)

## Features

- [x] Python 3.10
- [x] Pre-commit hooks for linting, formatting and testing - [pre-commit](https://pre-commit.com)
- [x] Logging Middleware for [structlog](https://github.com/hynek/structlog)
      and [asgi-correlation-id](https://github.com/snok/asgi-correlation-id).

- [x] Production deployment with gunicorn
- [x] Error reporting with Sentry
- [x] Isolated transactional database tests
- [x] HTTPSRedirectMiddleware; TrustedHostMiddleware; CORSMiddleware
- [x] Dependabot
- [x] Liveness and readiness endpoints
- [x] SQLAlchemy 2.0 style CRUD operations

## Usage Example

- Create `app_factory.py` on root level

```python
from fastapi import FastAPI
from fastapi_starter import FastAPIStarterTemplate

from .api.api_v1.api import api_router as api_v1_router
from .core.config import Settings, get_settings


class ThisFastAPI(FastAPIStarterTemplate):
    def init_settings(self) -> Settings:
        return get_settings()

    def configure_default_routes(self) -> None:
        self.app.include_router(api_v1_router, prefix=self.settings.API_V1_STR)


def create_app() -> FastAPI:
    return ThisFastAPI().create_app()
```

- Include default routes to your own `api.api_v1.api`

```python
from fastapi_starter.api.api_v1.api import api_router

from .endpoints import login, scopes, users

api_router.include_router(login.router, prefix="/login", tags=["login"])
api_router.include_router(scopes.router, prefix="/scopes", tags=["scopes"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
```

- Extend base settings class in your own `.core.config`

```python
from __future__ import annotations

from functools import lru_cache

from fastapi_starter.core.config import Settings as BaseSettings


@lru_cache
def get_settings() -> Settings:
    return Settings()


class Settings(BaseSettings):
    pass
```

## Configuration

- The application is configured with environment variables
  and will not start until all mandatory environment variables are passed.
- Application configuration source is `Settings` class from [src/fastapi_starter/core/config.py](src/fastapi_starter/core/config.py).
  It is a child class of `pydantic.BaseSettings` which allows configuration parameters
  to be automatically overridden by environment variables.
- Environment variables and secrets for development should
  be set on the container, e.g. in `docker-compose.yml`.
- For testing, [settings dependency](https://fastapi.tiangolo.com/advanced/settings/#settings-in-a-dependency)
  is overridden in [test fixtures](tests/conftest.py).
- In production, environment variables are set on the Docker container itself.
- With [Pydantic secret support](https://pydantic-docs.helpmanual.io/usage/settings/#secret-support),
  environment variables can be loaded from files in `/run/secrets`,
  which is handy if you use Docker Secrets.

## Installation

- Required software:

  - Python 3.10
  - [Python Poetry](https://python-poetry.org)

- Update global Python packages

```
python -m pip install -U pip wheel setuptools
```

- Install dependencies

```
poetry install
```

- Activate Python virtual environment

```
poetry shell
```

- Install pre-commit hooks

```
pre-commit install
```

## Development and testing

- Helper commands from [dev_scripts.py](src/fastapi_starter/util/dev_scripts.py)

```
poetry run format/lint/test/...
```

- Run all hooks at once

```
poetry run hooks
```

- Export artifacts from Docker Image

```
poetry run export-test-results/export-dist
```
