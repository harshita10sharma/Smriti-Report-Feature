from analysis.aggregation.engine import aggregate_rate
from analysis.models.enums import AggregationMethod, QualityStatus
from tests.fixtures.aggregation_fixtures import make_metric, obs


def test_valid_numerator_and_denominator() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    result = aggregate_rate(metric, "p1", obs([1.0, 1.0, 0.0, 0.0]))
    assert result.value == 0.5


def test_zero_denominator_is_unavailable() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    result = aggregate_rate(metric, "p1", [])
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE


def test_missing_denominator_entries_are_excluded_not_counted() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    result = aggregate_rate(metric, "p1", obs([1.0, None, 0.0]))
    assert result.value == 0.5
    assert result.missing_count == 1


def test_non_indicator_values_are_excluded_not_rounded() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    result = aggregate_rate(metric, "p1", obs([1.0, 0.0, 0.5]))
    assert result.value == 0.5  # 1 of 2 valid indicators
    assert len(result.excluded) == 1
    assert result.excluded[0].reason_code == "invalid_rate_indicator"


def test_result_is_always_bounded_zero_to_one() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    all_positive = aggregate_rate(metric, "p1", obs([1.0, 1.0, 1.0]))
    all_negative = aggregate_rate(metric, "p1", obs([0.0, 0.0, 0.0]))
    assert all_positive.value == 1.0
    assert all_negative.value == 0.0
    assert all_positive.value is not None and 0.0 <= all_positive.value <= 1.0
    assert all_negative.value is not None and 0.0 <= all_negative.value <= 1.0


def test_rate_is_never_negative() -> None:
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    result = aggregate_rate(metric, "p1", obs([0.0, 0.0, 1.0]))
    assert result.value is not None
    assert result.value >= 0.0


def test_out_of_declared_range_values_are_excluded_before_indicator_check() -> None:
    # A value like -5.0 fails the registry valid_range check first
    # (outside_valid_range), never reaching the indicator check.
    metric = make_metric(AggregationMethod.RATE, valid_range=(0.0, 1.0))
    result = aggregate_rate(metric, "p1", obs([1.0, -5.0]))
    assert result.value == 1.0
    assert result.excluded[0].reason_code == "outside_valid_range"
