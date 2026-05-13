from __future__ import annotations

import contextvars
import json
import logging
import time
import uuid
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse, Response

REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128

_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id",
    default=None,
)
_user_id: contextvars.ContextVar[int | None] = contextvars.ContextVar(
    "user_id",
    default=None,
)

request_logger = logging.getLogger("app.request")
business_logger = logging.getLogger("app.business")
exception_logger = logging.getLogger("app.exception")

_RESERVED_LOG_RECORD_ATTRS = set(logging.makeLogRecord({}).__dict__) | {
    "asctime",
    "message",
}


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname.lower(),
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_LOG_RECORD_ATTRS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type is not None:
                payload["exception"] = {"type": exc_type.__name__}
        return json.dumps(payload, default=str, separators=(",", ":"))


def configure_logging(level: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    if not root_logger.handlers:
        root_logger.addHandler(logging.StreamHandler())
    for handler in root_logger.handlers:
        handler.setFormatter(JsonLogFormatter())


def sanitize_request_id(value: str | None) -> str:
    request_id = (value or "").strip()
    if (
        not request_id
        or len(request_id) > MAX_REQUEST_ID_LENGTH
        or any(character in request_id for character in "\r\n")
    ):
        return str(uuid.uuid4())
    return request_id


def get_request_id(request: Request | None = None) -> str | None:
    if request is not None:
        state_request_id = getattr(request.state, "request_id", None)
        if state_request_id is not None:
            return state_request_id
    return _request_id.get()


def get_user_id(request: Request | None = None) -> int | None:
    if request is not None:
        state_user_id = getattr(request.state, "user_id", None)
        if state_user_id is not None:
            return state_user_id
    return _user_id.get()


def set_request_user(request: Request, user_id: int) -> None:
    request.state.user_id = user_id
    _user_id.set(user_id)


def log_business_event(
    event: str,
    *,
    request: Request | None = None,
    user_id: int | None = None,
    **fields: Any,
) -> None:
    resolved_user_id = user_id if user_id is not None else get_user_id(request)
    business_logger.info(
        event,
        extra={
            "event": event,
            "request_id": get_request_id(request),
            "user_id": resolved_user_id,
            **fields,
        },
    )


async def request_logging_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    request_id = sanitize_request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    request_id_token = _request_id.set(request_id)
    user_id_token = _user_id.set(None)
    start_time = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers[REQUEST_ID_HEADER] = request_id
        return response
    finally:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        user_id = get_user_id(request)
        request_logger.info(
            "api.request",
            extra={
                "event": "api.request",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "duration_ms": duration_ms,
                "request_id": request_id,
                "user_id": user_id,
            },
        )
        _request_id.reset(request_id_token)
        _user_id.reset(user_id_token)


def log_unhandled_exception(request: Request, exc: Exception) -> None:
    exception_logger.error(
        "api.unhandled_exception",
        exc_info=(type(exc), exc, exc.__traceback__),
        extra={
            "event": "api.unhandled_exception",
            "method": request.method,
            "path": request.url.path,
            "request_id": get_request_id(request),
            "user_id": get_user_id(request),
            "exception_type": type(exc).__name__,
        },
    )


def unhandled_exception_response(request: Request) -> JSONResponse:
    request_id = get_request_id(request)
    headers = {REQUEST_ID_HEADER: request_id} if request_id else None
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error."},
        headers=headers,
    )
