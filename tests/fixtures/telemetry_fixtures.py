"""Shared raw-telemetry fixtures for validation/adapter tests.

Every function returns a fresh dict/mapping so tests can mutate their
own copy without affecting other tests. Shapes are deliberately drawn
only from the reference backend's verified columns
(REPORT_READINESS_AUDIT.md S3) - nothing here invents a metrics
jsonb key as if it were confirmed telemetry.
"""

from __future__ import annotations

from typing import Any


def valid_event(**overrides: Any) -> dict[str, Any]:
    """A structurally and semantically valid raw event payload."""
    payload: dict[str, Any] = {
        "id": "event-1",
        "patient_id": "patient-1",
        "session_id": "session-1",
        "game_id": "market_basket",
        "domain": "memory",
        "ts": 1_700_000_000_000,
        "correct": True,
        "trial_index": 0,
        "response_time_ms": 850,
    }
    payload.update(overrides)
    return payload


def incomplete_event(**overrides: Any) -> dict[str, Any]:
    """Missing a required field (domain)."""
    payload = valid_event()
    del payload["domain"]
    payload.update(overrides)
    return payload


def malformed_event(**overrides: Any) -> dict[str, Any]:
    """A required field with the wrong type (ts as a non-numeric string)."""
    payload = valid_event(ts="not-a-timestamp")
    payload.update(overrides)
    return payload


def unknown_game_event(**overrides: Any) -> dict[str, Any]:
    """References a game_id this project has never seen or registered."""
    payload = valid_event(game_id="a_game_that_does_not_exist")
    payload.update(overrides)
    return payload


def negative_duration_event(**overrides: Any) -> dict[str, Any]:
    """A verified-column duration field with an impossible negative value."""
    payload = valid_event(response_time_ms=-100)
    payload.update(overrides)
    return payload


def undocumented_error_class_event(**overrides: Any) -> dict[str, Any]:
    """A non-empty error_class outside the documented vocabulary.

    error_class has no DB CHECK constraint (REPORT_READINESS_AUDIT.md
    S3), so this is valid telemetry that should downgrade to a
    warning, not an error.
    """
    payload = valid_event(correct=False, error_class="an_undocumented_value")
    payload.update(overrides)
    return payload


def duplicate_event_batch() -> list[dict[str, Any]]:
    """Two payloads sharing the same id - the second must be rejected."""
    first = valid_event(id="dup-1")
    second = valid_event(id="dup-1", trial_index=1)
    return [first, second]


def valid_session(**overrides: Any) -> dict[str, Any]:
    """A completed session envelope."""
    payload: dict[str, Any] = {
        "id": "session-1",
        "patient_id": "patient-1",
        "started_at": 1_700_000_000_000,
        "ended_at": 1_700_000_060_000,
        "game_ids": "market_basket",
        "completed": True,
    }
    payload.update(overrides)
    return payload


def partial_session(**overrides: Any) -> dict[str, Any]:
    """A session still in progress: no end time yet, not completed."""
    payload = valid_session(ended_at=None, completed=False)
    payload.update(overrides)
    return payload


def abandoned_session(**overrides: Any) -> dict[str, Any]:
    """A session the elder started but abandoned partway through."""
    payload = valid_session(
        ended_at=1_700_000_030_000,
        completed=False,
        abandoned_at_ms=1_700_000_025_000,
    )
    payload.update(overrides)
    return payload
