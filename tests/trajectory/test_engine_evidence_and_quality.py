from datetime import date

from analysis.models.enums import QualityStatus
from analysis.trajectory.config import MINIMUM_TRAJECTORY_POINTS
from analysis.trajectory.engine import estimate_trajectory
from tests.fixtures.baseline_fixtures import make_observation

_METRIC = "sort_harvest_perseverative_error_rate"
_AS_OF = date(2026, 1, 30)


def test_no_observations_at_all_is_unavailable() -> None:
    trajectory = estimate_trajectory("p1", _METRIC, [], _AS_OF)
    assert trajectory.quality == QualityStatus.UNAVAILABLE
    assert trajectory.points == ()
    assert trajectory.trend_direction is None
    assert trajectory.slope is None
    assert trajectory.r_squared is None


def test_only_unusable_observations_is_unavailable_not_zero() -> None:
    observations = [
        make_observation(
            "s1",
            date(2026, 1, 10),
            value=None,
            quality=QualityStatus.UNAVAILABLE,
            reason="metric gated",
        )
    ]
    trajectory = estimate_trajectory("p1", _METRIC, observations, _AS_OF)
    assert trajectory.quality == QualityStatus.UNAVAILABLE
    assert trajectory.points == ()
    assert trajectory.excluded_observation_ids == ("s1",)
    assert trajectory.exclusion_reasons == {"s1": "metric gated"}


def test_fewer_than_minimum_points_is_insufficient_but_keeps_points() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i)
        for i in range(MINIMUM_TRAJECTORY_POINTS - 1)
    ]
    trajectory = estimate_trajectory("p1", _METRIC, observations, _AS_OF)
    assert trajectory.quality == QualityStatus.INSUFFICIENT
    assert len(trajectory.points) == MINIMUM_TRAJECTORY_POINTS - 1
    assert trajectory.trend_direction is None
    assert trajectory.slope is None
    assert trajectory.r_squared is None


def test_exactly_minimum_points_is_sufficient_and_computes_a_trend() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i)
        for i in range(MINIMUM_TRAJECTORY_POINTS)
    ]
    trajectory = estimate_trajectory("p1", _METRIC, observations, _AS_OF)
    assert trajectory.quality == QualityStatus.SUFFICIENT
    assert len(trajectory.points) == MINIMUM_TRAJECTORY_POINTS
    assert trajectory.trend_direction is not None
    assert trajectory.slope is not None
    assert trajectory.r_squared is not None


def test_unusable_observations_are_excluded_with_provenance_but_do_not_block_usable_ones() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i)
        for i in range(MINIMUM_TRAJECTORY_POINTS)
    ] + [
        make_observation(
            "bad",
            date(2026, 1, 20),
            value=None,
            quality=QualityStatus.INSUFFICIENT,
            reason="below minimum trials",
        )
    ]
    trajectory = estimate_trajectory("p1", _METRIC, observations, _AS_OF)
    assert trajectory.quality == QualityStatus.SUFFICIENT
    assert trajectory.excluded_observation_ids == ("bad",)
    assert trajectory.exclusion_reasons == {"bad": "below minimum trials"}
    assert "bad" not in {
        oid for point in trajectory.points for oid in point.contributing_observation_ids
    }
