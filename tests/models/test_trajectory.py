from datetime import date

import pydantic
import pytest

from analysis.models.enums import Direction, QualityStatus
from analysis.models.trajectory import ChangePoint, Trajectory, TrajectoryPoint


def _make_point(**overrides: object) -> TrajectoryPoint:
    fields: dict[str, object] = {
        "period_start": date(2026, 1, 1),
        "period_end": date(2026, 1, 1),
        "raw_value": 1.0,
        "normalized_value": 0.5,
        "smoothed_value": None,
        "sample_count": 3,
        "quality": QualityStatus.SUFFICIENT,
    }
    fields.update(overrides)
    return TrajectoryPoint.model_validate(fields)


def _make_change_point(**overrides: object) -> ChangePoint:
    fields: dict[str, object] = {
        "metric_id": "m1",
        "changepoint_date": date(2026, 2, 1),
        "direction": Direction.LOWER_IS_BETTER,
        "magnitude": 1.2,
        "confidence": 0.8,
        "pre_change_window": (date(2026, 1, 1), date(2026, 1, 28)),
        "post_change_window": (date(2026, 2, 1), date(2026, 2, 28)),
        "detection_method": "ewma",
    }
    fields.update(overrides)
    return ChangePoint.model_validate(fields)


def test_point_with_zero_sample_count_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError):
        _make_point(sample_count=0)


def test_point_with_positive_sample_count_is_valid() -> None:
    point = _make_point()
    assert point.sample_count == 3


def test_change_point_defaults_persistent_to_none() -> None:
    change_point = _make_change_point()
    assert change_point.persistent is None


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_change_point_rejects_confidence_outside_probability_range(
    confidence: float,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        _make_change_point(confidence=confidence)


def test_trajectory_sample_count_sums_points() -> None:
    trajectory = Trajectory(
        patient_id="p1",
        metric_id="m1",
        points=(_make_point(sample_count=2), _make_point(sample_count=5)),
        smoothing_method=None,
        trend_direction=None,
        quality=QualityStatus.SUFFICIENT,
    )
    assert trajectory.sample_count == 7


def test_trajectory_defaults_to_no_change_points() -> None:
    trajectory = Trajectory(
        patient_id="p1",
        metric_id="m1",
        points=(),
        smoothing_method=None,
        trend_direction=None,
        quality=QualityStatus.INSUFFICIENT,
    )
    assert trajectory.change_points == ()
    assert trajectory.sample_count == 0
