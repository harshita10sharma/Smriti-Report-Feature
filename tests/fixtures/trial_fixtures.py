"""Shared Trial factory for game-analyzer tests."""

from __future__ import annotations

from typing import Any

from analysis.models.enums import Domain
from analysis.models.telemetry import Trial


def make_trial(**overrides: Any) -> Trial:
    fields: dict[str, Any] = {
        "event_id": "e1",
        "patient_id": "p1",
        "session_id": "s1",
        "game_id": "market_basket",
        "domain": Domain.MEMORY,
        "trial_index": 0,
        "item_id": None,
        "difficulty": None,
        "correct": True,
        "response_time_ms": 500,
        "error_class": None,
        "trial_context": None,
        "metrics": {},
        "ts": 1_700_000_000_000,
    }
    fields.update(overrides)
    return Trial.model_validate(fields)
