"""Structured logging setup.

Emits one JSON object per log line so pipeline-stage observability
(input counts, validation failures, processing duration, etc. - see
master spec S119) can be queried/aggregated without a separate log
parser. Deliberately never includes secret values; callers are
responsible for not passing them as log fields either.
"""

from __future__ import annotations

import json
import logging
import sys
from collections.abc import MutableMapping
from datetime import UTC, datetime
from typing import Any

_installed_handler: logging.Handler | None = None

#: Field names that must never appear in a log record's extra data.
#: Defence in depth: config/secret-handling code should not be passing
#: these to the logger in the first place.
_FORBIDDEN_FIELD_NAMES = {
    "password",
    "secret",
    "token",
    "api_key",
    "service_role_key",
}


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        extra = getattr(record, "fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


class _FieldGuardedLoggerAdapter(logging.LoggerAdapter[logging.Logger]):
    """Rejects forbidden field names before they reach the handler.

    Validation happens here (in the caller's stack) rather than in the
    formatter, because the stdlib logging module swallows exceptions
    raised inside a handler/formatter's ``emit``/``format`` (it prints
    them to stderr via ``handleError`` instead of propagating) - which
    would silently defeat a guard placed there.
    """

    def process(
        self, msg: object, kwargs: MutableMapping[str, Any]
    ) -> tuple[object, MutableMapping[str, Any]]:
        fields = kwargs.get("extra", {}).get("fields") if kwargs.get("extra") else None
        if fields:
            for key in fields:
                if key.lower() in _FORBIDDEN_FIELD_NAMES:
                    raise ValueError(
                        f"Refusing to log field '{key}': looks like a secret."
                    )
        return msg, kwargs


def configure_logging(level: str = "INFO") -> None:
    """Configure the root logger for structured JSON output.

    Safe to call more than once: any handler this function previously
    installed is replaced rather than stacked, and the new handler is
    always bound to the *current* ``sys.stdout`` (important for tests
    that redirect stdout, e.g. pytest's ``capsys``). Handlers installed
    by anything else (pytest's own log capture, for example) are left
    untouched.
    """
    global _installed_handler
    root = logging.getLogger()
    root.setLevel(level)
    if _installed_handler is not None:
        root.removeHandler(_installed_handler)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(_JsonFormatter())
    root.addHandler(handler)
    _installed_handler = handler


def get_logger(name: str) -> logging.LoggerAdapter[logging.Logger]:
    """Return a logger to use for structured, field-carrying log calls.

    Pass extra structured fields via ``extra={"fields": {...}}``, e.g.::

        logger.info("telemetry validated", extra={"fields": {
            "patient_id": patient_id, "valid_count": 42,
        }})

    Raises ``ValueError`` immediately if a field name looks like a
    secret (see ``_FORBIDDEN_FIELD_NAMES``).
    """
    return _FieldGuardedLoggerAdapter(logging.getLogger(name), {})
