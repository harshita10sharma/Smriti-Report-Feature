"""Shared factories for baseline-engine tests."""

from __future__ import annotations

from datetime import date
from typing import Any

from analysis.aggregation.models import AggregationResult
from analysis.baseline.models import BaselineObservation
from analysis.models.enums import AggregationMethod, GameId, QualityStatus


def make_aggregation_result(**overrides: Any) -> AggregationResult:
    fields: dict[str, Any] = {
        "metric_id": "sort_harvest_perseverative_error_rate",
        "patient_id": "p1",
        "game_id": GameId.SORT_THE_HARVEST,
        "aggregation": AggregationMethod.RATE,
        "value": 0.2,
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


def make_observation(
    session_id: str, observed_on: date, **result_overrides: Any
) -> BaselineObservation:
    return BaselineObservation(
        session_id=session_id,
        observed_on=observed_on,
        result=make_aggregation_result(**result_overrides),
    )
