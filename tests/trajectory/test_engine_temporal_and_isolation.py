from datetime import date

import pytest

from analysis.baseline.models import BaselineObservation
from analysis.errors import PatientIsolationError, RegistryError
from analysis.trajectory.engine import estimate_trajectory
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
    trajectory = estimate_trajectory("p1", _METRIC, _rich_observations(), date(2026, 1, 16))
    assert trajectory.sample_count == 6


def test_observation_exactly_at_cutoff_contributes() -> None:
    observations = [make_observation("s1", date(2026, 1, 15), value=0.5)]
    trajectory = estimate_trajectory("p1", _METRIC, observations, date(2026, 1, 15))
    assert trajectory.sample_count == 1


def test_observation_after_cutoff_is_excluded_entirely() -> None:
    future = make_observation("future", date(2026, 2, 1), value=0.5)
    observations = [*_rich_observations(), future]
    with_future = estimate_trajectory("p1", _METRIC, observations, date(2026, 1, 20))
    without_future = estimate_trajectory("p1", _METRIC, _rich_observations(), date(2026, 1, 20))
    assert with_future == without_future
    assert not any(
        "future" in point.contributing_observation_ids for point in with_future.points
    )


def test_future_observation_never_changes_a_historical_result() -> None:
    trajectory_no_future = estimate_trajectory("p1", _METRIC, _rich_observations(), _AS_OF)
    dramatic_future = make_observation("future", date(2026, 6, 1), value=999.0)
    trajectory_with_future = estimate_trajectory(
        "p1", _METRIC, [*_rich_observations(), dramatic_future], _AS_OF
    )
    assert trajectory_no_future == trajectory_with_future


def test_multiple_sessions_on_the_same_day_collapse_into_one_point() -> None:
    observations = [
        make_observation("a", date(2026, 1, 15), value=0.1),
        make_observation("b", date(2026, 1, 15), value=0.3),
    ]
    trajectory = estimate_trajectory("p1", _METRIC, observations, _AS_OF)
    assert len(trajectory.points) == 1
    assert trajectory.points[0].sample_count == 2
    assert trajectory.points[0].raw_value == 0.2  # median of 0.1 and 0.3
    assert trajectory.points[0].contributing_observation_ids == ("a", "b")


# --- DETERMINISM / ORDERING -----------------------------------------------------


def test_result_is_deterministic_regardless_of_input_order() -> None:
    observations = _rich_observations()
    reversed_observations = list(reversed(observations))
    forward = estimate_trajectory("p1", _METRIC, observations, _AS_OF)
    backward = estimate_trajectory("p1", _METRIC, reversed_observations, _AS_OF)
    assert forward == backward


# --- PATIENT ISOLATION ------------------------------------------------------------


def test_mismatched_patient_id_raises_patient_isolation_error() -> None:
    observations = _rich_observations(patient_id="patient-B")
    with pytest.raises(PatientIsolationError):
        estimate_trajectory("patient-A", _METRIC, observations, _AS_OF)


def test_two_patients_trajectories_are_independent() -> None:
    trajectory_a = estimate_trajectory(
        "patient-a", _METRIC, _rich_observations("patient-a", 0.0), _AS_OF
    )
    trajectory_b = estimate_trajectory(
        "patient-b", _METRIC, _rich_observations("patient-b", 10.0), _AS_OF
    )
    assert trajectory_a.patient_id == "patient-a"
    assert trajectory_b.patient_id == "patient-b"
    values_a = [point.raw_value for point in trajectory_a.points]
    values_b = [point.raw_value for point in trajectory_b.points]
    assert values_a != values_b


def test_mismatched_metric_id_raises_registry_error() -> None:
    observations = [
        make_observation("s1", date(2026, 1, 10), metric_id="my_day_orientation_accuracy")
    ]
    with pytest.raises(RegistryError):
        estimate_trajectory("p1", _METRIC, observations, _AS_OF)
