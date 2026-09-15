from datetime import date

import pytest

from analysis.baseline.engine import estimate_baseline
from analysis.baseline.models import BaselineObservation
from analysis.errors import PatientIsolationError, RegistryError
from tests.fixtures.baseline_fixtures import make_observation

_METRIC = "sort_harvest_perseverative_error_rate"
_AS_OF = date(2026, 1, 30)


def _rich_observations(
    patient_id: str = "p1", value_offset: float = 0.0
) -> list[BaselineObservation]:
    return [
        make_observation(
            f"s{i}", date(2026, 1, 10 + i), value=0.1 * i + value_offset, patient_id=patient_id
        )
        for i in range(6)
    ]


# --- TEMPORAL INTEGRITY -------------------------------------------------------


def test_observation_before_cutoff_contributes() -> None:
    baseline = estimate_baseline("p1", _METRIC, _rich_observations(), date(2026, 1, 16))
    assert baseline.n_sessions == 6


def test_observation_exactly_at_cutoff_contributes() -> None:
    observations = [make_observation("s1", date(2026, 1, 15), value=0.5)]
    baseline = estimate_baseline("p1", _METRIC, observations, date(2026, 1, 15))
    assert baseline.n_sessions == 1


def test_observation_after_cutoff_is_excluded_from_the_window_entirely() -> None:
    future = make_observation("future", date(2026, 2, 1), value=0.5)
    observations = [*_rich_observations(), future]
    with_future = estimate_baseline("p1", _METRIC, observations, date(2026, 1, 20))
    without_future = estimate_baseline("p1", _METRIC, _rich_observations(), date(2026, 1, 20))
    assert with_future.center == without_future.center
    assert with_future.n_sessions == without_future.n_sessions
    assert "future" not in with_future.contributing_observation_ids


def test_future_observation_never_changes_a_historical_result() -> None:
    baseline_no_future = estimate_baseline("p1", _METRIC, _rich_observations(), _AS_OF)
    dramatic_future = make_observation("future", date(2026, 6, 1), value=999.0)
    baseline_with_future = estimate_baseline(
        "p1", _METRIC, [*_rich_observations(), dramatic_future], _AS_OF
    )
    assert baseline_no_future == baseline_with_future


def test_duplicate_timestamps_do_not_break_ordering_or_counts() -> None:
    observations = [
        make_observation("a", date(2026, 1, 15), value=0.1),
        make_observation("b", date(2026, 1, 15), value=0.2),
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.n_sessions == 2
    assert baseline.n_days == 1


# --- DETERMINISM / ORDERING -----------------------------------------------------


def test_result_is_deterministic_regardless_of_input_order() -> None:
    observations = _rich_observations()
    reversed_observations = list(reversed(observations))
    forward = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    backward = estimate_baseline("p1", _METRIC, reversed_observations, _AS_OF)
    assert forward == backward


# --- PATIENT ISOLATION ------------------------------------------------------------


def test_mismatched_patient_id_raises_patient_isolation_error() -> None:
    observations = _rich_observations(patient_id="patient-B")
    with pytest.raises(PatientIsolationError):
        estimate_baseline("patient-A", _METRIC, observations, _AS_OF)


def test_two_patients_baselines_are_independent() -> None:
    baseline_a = estimate_baseline(
        "patient-a", _METRIC, _rich_observations("patient-a", 0.0), _AS_OF
    )
    baseline_b = estimate_baseline(
        "patient-b", _METRIC, _rich_observations("patient-b", 10.0), _AS_OF
    )
    assert baseline_a.patient_id == "patient-a"
    assert baseline_b.patient_id == "patient-b"
    assert baseline_a.center != baseline_b.center
    assert set(baseline_a.contributing_observation_ids) == set(
        baseline_b.contributing_observation_ids
    )  # same session ids reused across patients, but results stay independent


def test_mismatched_metric_id_raises_registry_error() -> None:
    observations = [
        make_observation("s1", date(2026, 1, 10), metric_id="my_day_orientation_accuracy")
    ]
    with pytest.raises(RegistryError):
        estimate_baseline("p1", _METRIC, observations, _AS_OF)
