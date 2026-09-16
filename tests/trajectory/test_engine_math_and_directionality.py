from datetime import date

from analysis.baseline.models import BaselineObservation
from analysis.models.enums import Direction, TrendDirection
from analysis.trajectory.engine import estimate_trajectory
from tests.fixtures.baseline_fixtures import make_observation

_METRIC = "sort_harvest_perseverative_error_rate"  # LOWER_IS_BETTER
_AS_OF = date(2026, 1, 30)


def _observations(values: list[float]) -> list[BaselineObservation]:
    return [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=value)
        for i, value in enumerate(values)
    ]


def test_clearly_increasing_values_are_classified_increasing() -> None:
    trajectory = estimate_trajectory(
        "p1", _METRIC, _observations([0.0, 0.5, 1.0, 1.5, 2.0]), _AS_OF
    )
    assert trajectory.slope is not None
    assert trajectory.slope > 0
    assert trajectory.trend_direction == TrendDirection.INCREASING


def test_clearly_decreasing_values_are_classified_decreasing() -> None:
    trajectory = estimate_trajectory(
        "p1", _METRIC, _observations([2.0, 1.5, 1.0, 0.5, 0.0]), _AS_OF
    )
    assert trajectory.slope is not None
    assert trajectory.slope < 0
    assert trajectory.trend_direction == TrendDirection.DECREASING


def test_constant_values_are_classified_stable_with_perfect_fit() -> None:
    trajectory = estimate_trajectory(
        "p1", _METRIC, _observations([0.4, 0.4, 0.4, 0.4]), _AS_OF
    )
    assert trajectory.trend_direction == TrendDirection.STABLE
    assert trajectory.slope == 0.0
    assert trajectory.r_squared == 1.0


def test_tiny_slope_relative_to_noise_is_classified_stable() -> None:
    # Values wobble across a wide range but only drift a hair over the
    # whole window - the drift should not be reported as a trend.
    trajectory = estimate_trajectory(
        "p1", _METRIC, _observations([0.40, 0.55, 0.35, 0.50, 0.401]), _AS_OF
    )
    assert trajectory.trend_direction == TrendDirection.STABLE


def test_metric_direction_is_populated_from_the_registry() -> None:
    trajectory = estimate_trajectory(
        "p1", _METRIC, _observations([0.0, 0.5, 1.0, 1.5]), _AS_OF
    )
    assert trajectory.metric_direction == Direction.LOWER_IS_BETTER


def test_trend_direction_never_reinterprets_metric_direction() -> None:
    # An INCREASING raw trend on a LOWER_IS_BETTER metric would be
    # unfavorable - the engine must report the neutral fact only, and
    # must not flip trend_direction or omit it to "protect" the reader.
    trajectory = estimate_trajectory(
        "p1", _METRIC, _observations([0.0, 0.5, 1.0, 1.5, 2.0]), _AS_OF
    )
    assert trajectory.trend_direction == TrendDirection.INCREASING
    assert trajectory.metric_direction == Direction.LOWER_IS_BETTER


def test_unregistered_metric_id_has_no_metric_direction() -> None:
    trajectory = estimate_trajectory("p1", "not_a_real_metric", [], _AS_OF)
    assert trajectory.metric_direction is None


def test_smoothing_method_label_is_present_only_once_a_trend_is_computed() -> None:
    insufficient = estimate_trajectory("p1", _METRIC, _observations([0.1, 0.2]), _AS_OF)
    sufficient = estimate_trajectory(
        "p1", _METRIC, _observations([0.1, 0.2, 0.3]), _AS_OF
    )
    assert insufficient.smoothing_method is None
    assert sufficient.smoothing_method == "ordinary_least_squares_on_daily_median"
