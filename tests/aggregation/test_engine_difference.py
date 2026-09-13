from analysis.aggregation.engine import aggregate_difference
from analysis.models.enums import AggregationMethod, QualityStatus
from tests.fixtures.aggregation_fixtures import make_metric, obs


def test_valid_pre_and_post() -> None:
    metric = make_metric(AggregationMethod.DIFFERENCE)
    result = aggregate_difference(metric, "p1", obs([1.0, 2.0]), obs([5.0, 6.0]))
    # after summary (5.5) - before summary (1.5) = 4.0
    assert result.value == 4.0
    assert result.quality == QualityStatus.SUFFICIENT


def test_missing_before_group_is_unavailable() -> None:
    metric = make_metric(AggregationMethod.DIFFERENCE)
    result = aggregate_difference(metric, "p1", [], obs([5.0, 6.0]))
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE


def test_missing_after_group_is_unavailable() -> None:
    metric = make_metric(AggregationMethod.DIFFERENCE)
    result = aggregate_difference(metric, "p1", obs([1.0, 2.0]), [])
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE


def test_before_group_with_only_missing_values_is_unavailable() -> None:
    metric = make_metric(AggregationMethod.DIFFERENCE)
    result = aggregate_difference(metric, "p1", obs([None, None]), obs([5.0, 6.0]))
    assert result.value is None


def test_negative_difference_is_meaningful_not_invalid() -> None:
    # Getting faster (post < pre) is a legitimate, informative negative
    # difference - it must not be excluded or treated as an error.
    metric = make_metric(AggregationMethod.DIFFERENCE)
    result = aggregate_difference(metric, "p1", obs([10.0, 12.0]), obs([2.0, 4.0]))
    assert result.value == -8.0
    assert result.quality == QualityStatus.SUFFICIENT


def test_median_combine_mode() -> None:
    metric = make_metric(AggregationMethod.DIFFERENCE)
    result = aggregate_difference(
        metric, "p1", obs([1.0, 2.0, 100.0]), obs([5.0, 6.0, 7.0]), combine="median"
    )
    assert result.value == 6.0 - 2.0


def test_computed_value_outside_declared_range_downgrades_to_limited() -> None:
    # valid_range here describes the *difference itself*, not the raw
    # pre/post values - it must not be applied to the raw inputs.
    metric = make_metric(AggregationMethod.DIFFERENCE, valid_range=(-1.0, 1.0))
    result = aggregate_difference(metric, "p1", obs([1.0, 2.0]), obs([50.0, 60.0]))
    assert result.value == 53.5
    assert result.quality == QualityStatus.LIMITED
    assert result.reason is not None
    assert "outside the metric's expected valid_range" in result.reason


def test_raw_input_values_are_not_filtered_by_the_difference_range() -> None:
    # Individual pre/post values of 50-60 would fail a (-1, 1) range
    # check if it were (incorrectly) applied per-value; confirm they
    # are NOT excluded, only the final computed value is flagged.
    metric = make_metric(AggregationMethod.DIFFERENCE, valid_range=(-1.0, 1.0))
    result = aggregate_difference(metric, "p1", obs([1.0, 2.0]), obs([50.0, 60.0]))
    assert result.excluded == ()
    assert result.valid_count == 4


def test_below_minimum_observations_is_insufficient() -> None:
    metric = make_metric(AggregationMethod.DIFFERENCE, minimum_observations=10)
    result = aggregate_difference(metric, "p1", obs([1.0]), obs([5.0]))
    assert result.quality == QualityStatus.INSUFFICIENT
    assert result.value is None
