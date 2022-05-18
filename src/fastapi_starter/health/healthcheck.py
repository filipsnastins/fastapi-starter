import http.client
import json
import logging
import sys
from urllib.parse import urljoin

import structlog

from ..core.config import get_settings

logging.basicConfig(stream=sys.stdout, level=logging.ERROR)
logger: structlog.stdlib.BoundLogger = structlog.get_logger()


def run_healthcheck() -> None:
    settings = get_settings()
    host = "localhost"
    port = settings.PORT
    endpoint = urljoin(settings.ROOT_PATH, settings.HEALTHCHECK_ENDPOINT)

    conn = http.client.HTTPConnection(host=host, port=port)
    conn.request("GET", endpoint)

    res = conn.getresponse()
    body = json.load(res)
    log = logger.bind(host=host, port=port, endpoint=endpoint, status_code=res.status, body=body)
    if res.status != 200:
        log.error("healthcheck_failed")
        sys.exit(1)
    log.info("healthcheck_passed")
    sys.exit(0)


if __name__ == "__main__":
    run_healthcheck()
