from __future__ import annotations

import json
import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings

_REQUEST_LOGGER = logging.getLogger("pancreatic_signal.request")


def configure_logging() -> None:
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(level=level, format="%(message)s")

    root_logger.setLevel(level)
    _REQUEST_LOGGER.setLevel(level)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get(settings.request_id_header_name) or str(uuid4())
        request.state.request_id = request_id
        started = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration_ms = round((perf_counter() - started) * 1000, 2)
            _REQUEST_LOGGER.exception(
                json.dumps(
                    _request_log_payload(
                        request=request,
                        request_id=request_id,
                        duration_ms=duration_ms,
                        event="request_failed",
                        status_code=500,
                    )
                )
            )
            raise

        duration_ms = round((perf_counter() - started) * 1000, 2)
        response.headers[settings.request_id_header_name] = request_id
        _REQUEST_LOGGER.info(
            json.dumps(
                _request_log_payload(
                    request=request,
                    request_id=request_id,
                    duration_ms=duration_ms,
                    event="request_completed",
                    status_code=response.status_code,
                )
            )
        )
        return response


def _request_log_payload(
    *,
    request: Request,
    request_id: str,
    duration_ms: float,
    event: str,
    status_code: int,
) -> dict[str, object]:
    return {
        "event": event,
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query or None,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "client": request.client.host if request.client else None,
        "environment": settings.app_env,
    }
