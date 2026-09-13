import pytest

from analysis.aggregation.engine import aggregate_mean, aggregate_median, aggregate_stddev
from analysis.models.enums import AggregationMethod, QualityStatus
from tests.fixtures.aggregation_fixtures import make_metric, obs

# --- MEAN -------------------------------------------------------------


def test_mean_of_normal_values() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    result = aggregate_mean(metric, "p1", obs([1.0, 2.0, 3.0]))
    assert result.value == 2.0
    assert result.quality == QualityStatus.SUFFICIENT


def test_mean_excludes_missing_values() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    result = aggregate_mean(metric, "p1", obs([1.0, None, 3.0]))
    assert result.value == 2.0
    assert result.missing_count == 1


def test_mean_excludes_invalid_range_values() -> None:
    metric = make_metric(AggregationMethod.MEAN, valid_range=(0.0, 10.0))
    result = aggregate_mean(metric, "p1", obs([1.0, 2.0, 999.0]))
    assert result.value == 1.5
    assert len(result.excluded) == 1
    assert result.excluded[0].reason_code == "outside_valid_range"


def test_mean_empty_input_is_unavailable() -> None:
    metric = make_metric(AggregationMethod.MEAN)
    result = aggregate_mean(metric, "p1", [])
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE


def test_mean_mixed_quality_below_minimum_is_insufficient() -> None:
    metric = make_metric(AggregationMethod.MEAN, minimum_observations=5)
    result = aggregate_mean(metric, "p1", obs([1.0, 2.0]))
    assert result.value is None
    assert result.quality == QualityStatus.INSUFFICIENT


# --- MEDIAN -------------------------------------------------------------


def test_median_odd_sample_count() -> None:
    metric = make_metric(AggregationMethod.MEDIAN)
    result = aggregate_median(metric, "p1", obs([3.0, 1.0, 2.0]))
    assert result.value == 2.0


def test_median_even_sample_count() -> None:
    metric = make_metric(AggregationMethod.MEDIAN)
    result = aggregate_median(metric, "p1", obs([1.0, 2.0, 3.0, 4.0]))
    assert result.value == 2.5


def test_median_excludes_missing_values() -> None:
    metric = make_metric(AggregationMethod.MEDIAN)
    result = aggregate_median(metric, "p1", obs([1.0, None, None, 4.0]))
    assert result.value == 2.5
    assert result.missing_count == 2


def test_median_insufficient_evidence() -> None:
    metric = make_metric(AggregationMethod.MEDIAN, minimum_observations=3)
    result = aggregate_median(metric, "p1", obs([1.0]))
    assert result.quality == QualityStatus.INSUFFICIENT
    assert result.value is None


# --- STDDEV -------------------------------------------------------------


def test_stddev_sufficient_sample() -> None:
    metric = make_metric(AggregationMethod.STDDEV, minimum_observations=2)
    result = aggregate_stddev(metric, "p1", obs([1.0, 2.0, 3.0]))
    assert result.value is not None and result.value > 0
    assert result.quality == QualityStatus.SUFFICIENT


def test_stddev_one_observation_is_insufficient_when_minimum_is_two() -> None:
    metric = make_metric(AggregationMethod.STDDEV, minimum_observations=2)
    result = aggregate_stddev(metric, "p1", obs([5.0]))
    assert result.value is None
    assert result.quality == QualityStatus.INSUFFICIENT


def test_stddev_empty_input() -> None:
    metric = make_metric(AggregationMethod.STDDEV, minimum_observations=2)
    result = aggregate_stddev(metric, "p1", [])
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE


def test_stddev_is_never_negative() -> None:
    metric = make_metric(AggregationMethod.STDDEV, minimum_observations=2)
    result = aggregate_stddev(metric, "p1", obs([10.0, 10.0, 10.0]))
    assert result.value == 0.0


@pytest.mark.parametrize("values", [[1.0, 5.0, 2.0, 9.0], [3.0, 3.0], [-2.0, 4.0, 1.5]])
def test_stddev_invariant_never_negative(values: list[float]) -> None:
    metric = make_metric(AggregationMethod.STDDEV, minimum_observations=2)
    result = aggregate_stddev(metric, "p1", obs(values))
    assert result.value is not None
    assert result.value >= 0.0
