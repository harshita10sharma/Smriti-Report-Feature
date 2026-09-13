import pydantic
import pytest

from analysis.aggregation.models import AggregationResult, ExcludedObservation, RawObservation
from analysis.models.enums import AggregationMethod, GameId, QualityStatus


def test_raw_observation_accepts_a_present_value() -> None:
    obs = RawObservation(source_id="e1", ts=1, value=0.5)
    assert obs.value == 0.5


def test_raw_observation_accepts_a_missing_value() -> None:
    obs = RawObservation(source_id="e1", ts=1, value=None)
    assert obs.value is None


@pytest.mark.parametrize("bad_value", [float("nan"), float("inf"), float("-inf")])
def test_raw_observation_rejects_non_finite_values(bad_value: float) -> None:
    with pytest.raises(pydantic.ValidationError, match="must be finite"):
        RawObservation(source_id="e1", ts=1, value=bad_value)


def test_raw_observation_is_immutable() -> None:
    obs = RawObservation(source_id="e1", ts=1, value=0.5)
    with pytest.raises(pydantic.ValidationError):
        obs.value = 0.9


def _make_result(**overrides: object) -> AggregationResult:
    fields: dict[str, object] = {
        "metric_id": "m1",
        "patient_id": "p1",
        "game_id": GameId.MY_DAY,
        "aggregation": AggregationMethod.RATE,
        "value": 0.5,
        "quality": QualityStatus.SUFFICIENT,
        "reason": None,
        "valid_count": 2,
        "missing_count": 0,
        "excluded": (),
        "source_ids": ("e1", "e2"),
        "ts_range": (1, 2),
    }
    fields.update(overrides)
    return AggregationResult.model_validate(fields)


def test_valid_result_round_trips() -> None:
    result = _make_result()
    assert result.value == 0.5


def test_missing_value_without_reason_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="reason is required"):
        _make_result(value=None, quality=QualityStatus.UNAVAILABLE, reason=None)


def test_missing_value_with_reason_is_valid() -> None:
    result = _make_result(
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        reason="no observations supplied",
        valid_count=0,
        source_ids=(),
        ts_range=None,
    )
    assert result.value is None


@pytest.mark.parametrize(
    ("field", "value"),
    [("valid_count", -1), ("missing_count", -1)],
)
def test_negative_counts_are_rejected(field: str, value: int) -> None:
    with pytest.raises(pydantic.ValidationError, match="must not be negative"):
        _make_result(**{field: value})


def test_ts_range_with_min_greater_than_max_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError, match="min > max"):
        _make_result(ts_range=(5, 1))


def test_excluded_observations_are_preserved() -> None:
    excluded = ExcludedObservation(
        source_id="e3", reason_code="outside_valid_range", reason_message="value was 2.0"
    )
    result = _make_result(excluded=(excluded,))
    assert result.excluded[0].reason_code == "outside_valid_range"
