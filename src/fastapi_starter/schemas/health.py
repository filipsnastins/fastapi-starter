from pydantic import BaseModel  # pylint: disable=no-name-in-module


class Health(BaseModel):
    healthy: bool


class ReadinessChecks(BaseModel):
    database_connection: bool


class Readiness(BaseModel):
    ready: bool
    checks: ReadinessChecks
