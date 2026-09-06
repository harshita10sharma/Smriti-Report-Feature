import pydantic
import pytest

from analysis.models.enums import (
    AggregationMethod,
    Direction,
    Domain,
    GameId,
    MetricType,
    TelemetrySource,
)
from analysis.registry.metrics import RegisteredMetric


def _make_metric(**overrides: object) -> RegisteredMetric:
    fields: dict[str, object] = {
        "metric_id": "switch_cost_ms",
        "display_name": "Switch cost",
        "description": "Post-switch minus pre-switch reaction time.",
        "unit": "ms",
        "direction": Direction.LOWER_IS_BETTER,
        "metric_type": MetricType.BEHAVIOURAL,
        "domain": Domain.EXECUTIVE,
        "game_id": GameId.SORT_THE_HARVEST,
        "aggregation": AggregationMethod.DIFFERENCE,
        "telemetry_source": TelemetrySource.VERIFIED_COLUMN,
        "required_fields": ("trial_context", "response_time_ms"),
        "verification_note": "trial_context and response_time_ms are verified columns.",
    }
    fields.update(overrides)
    return RegisteredMetric.model_validate(fields)


def test_valid_verified_metric() -> None:
    metric = _make_metric()
    assert metric.telemetry_source is TelemetrySource.VERIFIED_COLUMN


def test_jsonb_field_without_unverified_source_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="not METRICS_JSONB_UNVERIFIED"):
        _make_metric(required_fields=("metrics.stroke_velocity",))


def test_unverified_source_without_jsonb_field_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="no required_fields entry"):
        _make_metric(
            telemetry_source=TelemetrySource.METRICS_JSONB_UNVERIFIED,
            required_fields=("response_time_ms",),
        )


def test_unverified_source_with_jsonb_field_is_valid() -> None:
    metric = _make_metric(
        telemetry_source=TelemetrySource.METRICS_JSONB_UNVERIFIED,
        required_fields=("metrics.stroke_velocity",),
    )
    assert metric.telemetry_source is TelemetrySource.METRICS_JSONB_UNVERIFIED


def test_empty_required_fields_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="must not be empty"):
        _make_metric(required_fields=())
