from datetime import date

import pytest

from analysis.baseline.engine import assess_practice_effect
from analysis.errors import PatientIsolationError
from analysis.models.enums import QualityStatus
from tests.fixtures.baseline_fixtures import make_observation

_METRIC = "sort_harvest_perseverative_error_rate"
_AS_OF = date(2026, 1, 30)


def test_insufficient_observations_yields_insufficient_status_and_empty_trajectory() -> None:
    observations = [make_observation("s1", date(2026, 1, 10), value=0.1)]
    assessment = assess_practice_effect("p1", _METRIC, observations, _AS_OF)
    assert assessment.status == QualityStatus.INSUFFICIENT
    assert assessment.raw_trajectory == ()
    assert assessment.reason is not None


def test_sufficient_observations_yields_ordered_raw_trajectory() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    assessment = assess_practice_effect("p1", _METRIC, observations, _AS_OF)
    assert assessment.status == QualityStatus.SUFFICIENT
    assert len(assessment.raw_trajectory) == 6
    dates = [point.observed_on for point in assessment.raw_trajectory]
    assert dates == sorted(dates)


def test_no_correction_is_ever_applied() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    assessment = assess_practice_effect("p1", _METRIC, observations, _AS_OF)
    assert assessment.correction_applied is False


def test_raw_trajectory_values_are_unmodified_from_the_source_results() -> None:
    observations = [
        make_observation("s0", date(2026, 1, 10), value=0.42),
        make_observation("s1", date(2026, 1, 11), value=0.11),
        make_observation("s2", date(2026, 1, 12), value=0.99),
        make_observation("s3", date(2026, 1, 13), value=0.05),
        make_observation("s4", date(2026, 1, 14), value=0.77),
    ] + [make_observation("s5", date(2026, 1, 15), value=0.33)]
    assessment = assess_practice_effect("p1", _METRIC, observations, _AS_OF)
    values_by_session = {point.session_id: point.value for point in assessment.raw_trajectory}
    assert values_by_session["s0"] == 0.42
    assert values_by_session["s3"] == 0.05


def test_unavailable_observations_are_excluded_from_the_trajectory_not_imputed() -> None:
    gap = make_observation(
        "gap", date(2026, 1, 16), value=None, quality="unavailable",
        reason="gated", valid_count=0, source_ids=(), ts_range=None,
    )
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ] + [gap]
    assessment = assess_practice_effect("p1", _METRIC, observations, _AS_OF)
    session_ids = {point.session_id for point in assessment.raw_trajectory}
    assert "gap" not in session_ids
    assert len(assessment.raw_trajectory) == 6


def test_future_observation_does_not_affect_trajectory() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    future = make_observation("future", date(2026, 6, 1), value=999.0)
    without_future = assess_practice_effect("p1", _METRIC, observations, _AS_OF)
    with_future = assess_practice_effect("p1", _METRIC, [*observations, future], _AS_OF)
    assert without_future == with_future


def test_mismatched_patient_id_raises_patient_isolation_error() -> None:
    observations = [make_observation("s1", date(2026, 1, 10), patient_id="patient-B")]
    with pytest.raises(PatientIsolationError):
        assess_practice_effect("patient-A", _METRIC, observations, _AS_OF)
