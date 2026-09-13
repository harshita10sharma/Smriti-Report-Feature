"""Shared factories for aggregation-engine tests."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from analysis.aggregation.models import RawObservation
from analysis.models.enums import (
    AggregationMethod,
    Direction,
    Domain,
    GameId,
    MetricType,
    TelemetrySource,
)
from analysis.registry.metrics import RegisteredMetric


def make_metric(aggregation: AggregationMethod, **overrides: Any) -> RegisteredMetric:
    fields: dict[str, Any] = {
        "metric_id": "test_metric",
        "display_name": "Test metric",
        "description": "A synthetic metric for aggregation-engine tests.",
        "unit": "unit",
        "direction": Direction.HIGHER_IS_BETTER,
        "metric_type": MetricType.PERFORMANCE,
        "domain": Domain.MEMORY,
        "game_id": GameId.MY_DAY,
        "aggregation": aggregation,
        "telemetry_source": TelemetrySource.VERIFIED_COLUMN,
        "required_fields": ("correct",),
        "verification_note": "Synthetic metric for testing.",
        "minimum_observations": 1,
    }
    fields.update(overrides)
    return RegisteredMetric.model_validate(fields)


def obs(values: Sequence[float | None], *, start_ts: int = 0) -> list[RawObservation]:
    return [
        RawObservation(source_id=f"o{i}", ts=start_ts + i, value=v)
        for i, v in enumerate(values)
    ]
