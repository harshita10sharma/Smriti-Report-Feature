import pydantic
import pytest

from analysis.models.enums import Direction, Domain, MetricType, QualityStatus
from analysis.models.metrics import MetricDefinition, MetricObservation


def _make_definition(**overrides: object) -> MetricDefinition:
    fields: dict[str, object] = {
        "metric_id": "switch_cost_ms",
        "display_name": "Switch cost",
        "description": "Post-switch minus pre-switch reaction time.",
        "unit": "ms",
        "direction": Direction.LOWER_IS_BETTER,
        "metric_type": MetricType.BEHAVIOURAL,
        "domain": Domain.EXECUTIVE,
        "source_games": ("sort_the_harvest",),
    }
    fields.update(overrides)
    return MetricDefinition.model_validate(fields)


def test_definition_defaults() -> None:
    definition = _make_definition()
    assert definition.minimum_observations == 1
    assert definition.supports_baseline_normalization is True
    assert definition.supports_practice_effect_correction is False


def test_definition_is_immutable() -> None:
    definition = _make_definition()
    with pytest.raises(pydantic.ValidationError):
        definition.unit = "seconds"


def test_observation_with_value_needs_no_reason() -> None:
    observation = MetricObservation(
        metric_id="switch_cost_ms",
        patient_id="p1",
        session_id="s1",
        event_id="e1",
        game_id="sort_the_harvest",
        value=120.0,
        quality=QualityStatus.SUFFICIENT,
        unavailable_reason=None,
        ts=1,
    )
    assert observation.value == 120.0


def test_observation_missing_value_requires_reason() -> None:
    with pytest.raises(pydantic.ValidationError, match="unavailable_reason is required"):
        MetricObservation(
            metric_id="switch_cost_ms",
            patient_id="p1",
            session_id="s1",
            event_id=None,
            game_id="sort_the_harvest",
            value=None,
            quality=QualityStatus.UNAVAILABLE,
            unavailable_reason=None,
            ts=1,
        )


def test_observation_missing_value_with_reason_is_valid() -> None:
    observation = MetricObservation(
        metric_id="switch_cost_ms",
        patient_id="p1",
        session_id="s1",
        event_id=None,
        game_id="sort_the_harvest",
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        unavailable_reason="no post-switch trial_context recorded",
        ts=1,
    )
    assert observation.value is None
    assert observation.unavailable_reason is not None
