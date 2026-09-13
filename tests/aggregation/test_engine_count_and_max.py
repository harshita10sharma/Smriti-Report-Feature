import pytest

from analysis.aggregation.engine import aggregate_count, aggregate_max_achieved
from analysis.aggregation.models import RawObservation
from analysis.models.enums import AggregationMethod, QualityStatus, TelemetrySource
from tests.fixtures.aggregation_fixtures import make_metric, obs

# --- COUNT --------------------------------------------------------------


def test_count_valid_entities() -> None:
    metric = make_metric(AggregationMethod.COUNT)
    result = aggregate_count(metric, "p1", obs([1.0, 1.0, 1.0]))
    assert result.value == 3.0


def test_count_excludes_missing_entries() -> None:
    metric = make_metric(AggregationMethod.COUNT)
    result = aggregate_count(metric, "p1", obs([1.0, None, 1.0]))
    assert result.value == 2.0
    assert result.missing_count == 1


def test_count_duplicate_source_ids_are_each_counted() -> None:
    # A metric's caller is responsible for only supplying one
    # RawObservation per genuinely countable entity - the engine
    # itself has no identity concept beyond what it is given.
    metric = make_metric(AggregationMethod.COUNT)
    duplicated = [
        RawObservation(source_id="same-id", ts=1, value=1.0),
        RawObservation(source_id="same-id", ts=2, value=1.0),
    ]
    result = aggregate_count(metric, "p1", duplicated)
    assert result.value == 2.0


def test_count_is_never_negative() -> None:
    metric = make_metric(AggregationMethod.COUNT)
    result = aggregate_count(metric, "p1", [])
    assert result.value is None  # unavailable, not a negative/zero count
    assert result.quality == QualityStatus.UNAVAILABLE


def test_count_excludes_out_of_range_values() -> None:
    metric = make_metric(AggregationMethod.COUNT, valid_range=(0.0, 1.0))
    result = aggregate_count(metric, "p1", obs([1.0, 1.0, 5.0]))
    assert result.value == 2.0
    assert len(result.excluded) == 1


# --- MAX_ACHIEVED ---------------------------------------------------------


def test_max_achieved_increasing_span() -> None:
    metric = make_metric(AggregationMethod.MAX_ACHIEVED)
    result = aggregate_max_achieved(metric, "p1", obs([3.0, 4.0, 5.0, 2.0]))
    assert result.value == 5.0


def test_max_achieved_duplicate_spans() -> None:
    metric = make_metric(AggregationMethod.MAX_ACHIEVED)
    result = aggregate_max_achieved(metric, "p1", obs([4.0, 4.0, 4.0]))
    assert result.value == 4.0


def test_max_achieved_excludes_invalid_values() -> None:
    metric = make_metric(AggregationMethod.MAX_ACHIEVED, valid_range=(0.0, 10.0))
    result = aggregate_max_achieved(metric, "p1", obs([3.0, 4.0, 999.0]))
    assert result.value == 4.0
    assert len(result.excluded) == 1


def test_max_achieved_unavailable_when_gated() -> None:
    metric = make_metric(
        AggregationMethod.MAX_ACHIEVED,
        telemetry_source=TelemetrySource.METRICS_JSONB_UNVERIFIED,
        required_fields=("metrics.direction",),
    )
    with pytest.raises(AssertionError, match="attempted to aggregate"):
        aggregate_max_achieved(metric, "p1", obs([3.0, 4.0]))


def test_max_achieved_empty_input_is_unavailable() -> None:
    metric = make_metric(AggregationMethod.MAX_ACHIEVED)
    result = aggregate_max_achieved(metric, "p1", [])
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE
