from __future__ import annotations

import logging
from types import SimpleNamespace

from app.core.observability import (
    REQUEST_ID_HEADER,
    log_unhandled_exception,
    sanitize_request_id,
    unhandled_exception_response,
)


def test_sanitize_request_id_rejects_header_injection_and_oversized_values() -> None:
    assert sanitize_request_id(" request-123 ") == "request-123"

    generated_for_newline = sanitize_request_id("request\r\nmalicious")
    generated_for_oversized = sanitize_request_id("x" * 129)

    assert generated_for_newline != "request\r\nmalicious"
    assert generated_for_oversized != "x" * 129
    assert len(generated_for_newline) == 36
    assert len(generated_for_oversized) == 36


def test_unhandled_exception_logging_and_response_include_request_context(
    caplog,
) -> None:
    request = SimpleNamespace(
        method="GET",
        url=SimpleNamespace(path="/explode"),
        state=SimpleNamespace(request_id="exception-request-id", user_id=42),
    )
    exc = RuntimeError("boom")

    with caplog.at_level(logging.ERROR, logger="app.exception"):
        log_unhandled_exception(request, exc)

    record = next(
        item
        for item in caplog.records
        if getattr(item, "event", None) == "api.unhandled_exception"
    )
    assert record.method == "GET"
    assert record.path == "/explode"
    assert record.request_id == "exception-request-id"
    assert record.user_id == 42
    assert record.exception_type == "RuntimeError"

    response = unhandled_exception_response(request)

    assert response.status_code == 500
    assert response.headers[REQUEST_ID_HEADER] == "exception-request-id"
