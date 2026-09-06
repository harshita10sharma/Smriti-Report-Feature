from datetime import date

import pydantic
import pytest

from analysis.models.baseline import Baseline
from analysis.models.enums import BaselineStatus


def test_established_baseline_with_all_required_fields_is_valid() -> None:
    baseline = Baseline(
        patient_id="p1",
        metric_id="m1",
        status=BaselineStatus.ESTABLISHED,
        period_start=date(2026, 1, 1),
        period_end=date(2026, 1, 28),
        n_sessions=20,
        n_days=25,
        center=1.0,
        variability=0.2,
    )
    assert baseline.status is BaselineStatus.ESTABLISHED


@pytest.mark.parametrize("status", [BaselineStatus.ESTABLISHING, BaselineStatus.INSUFFICIENT_DATA])
def test_non_established_baseline_must_not_expose_estimate_values(
    status: BaselineStatus,
) -> None:
    with pytest.raises(pydantic.ValidationError):
        Baseline(
            patient_id="p1",
            metric_id="m1",
            status=status,
            period_start=None,
            period_end=None,
            n_sessions=1,
            n_days=1,
            center=1.0,
            variability=0.2,
        )


def test_non_established_baseline_without_estimate_values_is_valid() -> None:
    baseline = Baseline(
        patient_id="p1",
        metric_id="m1",
        status=BaselineStatus.INSUFFICIENT_DATA,
        period_start=None,
        period_end=None,
        n_sessions=1,
        n_days=1,
        center=None,
        variability=None,
    )
    assert baseline.center is None


def test_established_baseline_missing_center_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError):
        Baseline(
            patient_id="p1",
            metric_id="m1",
            status=BaselineStatus.ESTABLISHED,
            period_start=date(2026, 1, 1),
            period_end=date(2026, 1, 28),
            n_sessions=20,
            n_days=25,
            center=None,
            variability=0.2,
        )


def test_excluded_observation_without_reason_is_rejected() -> None:
    with pytest.raises(pydantic.ValidationError):
        Baseline(
            patient_id="p1",
            metric_id="m1",
            status=BaselineStatus.INSUFFICIENT_DATA,
            period_start=None,
            period_end=None,
            n_sessions=1,
            n_days=1,
            center=None,
            variability=None,
            excluded_observation_ids=("obs-1",),
            exclusion_reasons={},
        )


def test_excluded_observation_with_reason_is_valid() -> None:
    baseline = Baseline(
        patient_id="p1",
        metric_id="m1",
        status=BaselineStatus.INSUFFICIENT_DATA,
        period_start=None,
        period_end=None,
        n_sessions=1,
        n_days=1,
        center=None,
        variability=None,
        excluded_observation_ids=("obs-1",),
        exclusion_reasons={"obs-1": "response_time_ms outside plausible range"},
    )
    assert baseline.exclusion_reasons["obs-1"]
