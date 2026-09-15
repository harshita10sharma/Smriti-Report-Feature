"""Shared factory for domain-engine tests."""

from __future__ import annotations

from typing import Any

from analysis.aggregation.models import AggregationResult
from analysis.models.enums import AggregationMethod, GameId, QualityStatus


def make_result(metric_id: str, game_id: GameId, **overrides: Any) -> AggregationResult:
    fields: dict[str, Any] = {
        "metric_id": metric_id,
        "patient_id": "p1",
        "game_id": game_id,
        "aggregation": AggregationMethod.RATE,
        "value": 0.5,
        "quality": QualityStatus.SUFFICIENT,
        "reason": None,
        "valid_count": 4,
        "missing_count": 0,
        "excluded": (),
        "source_ids": ("e1", "e2", "e3", "e4"),
        "ts_range": (1, 4),
    }
    fields.update(overrides)
    return AggregationResult.model_validate(fields)
