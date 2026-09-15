from datetime import date

from analysis.baseline.engine import estimate_baseline
from analysis.baseline.models import BaselineObservation
from analysis.models.enums import BaselineStatus
from tests.fixtures.baseline_fixtures import make_observation

_METRIC = "sort_harvest_perseverative_error_rate"
_AS_OF = date(2026, 1, 30)


def _unavailable_obs(session_id: str, day: date) -> BaselineObservation:
    return make_observation(
        session_id, day, value=None, quality="unavailable",
        reason="gated", valid_count=0, source_ids=(), ts_range=None,
    )


def _insufficient_obs(session_id: str, day: date) -> BaselineObservation:
    return make_observation(
        session_id, day, value=None, quality="insufficient",
        reason="not enough trials", valid_count=0, source_ids=(), ts_range=None,
    )


# --- QUALITY PROPAGATION -----------------------------------------------------


def test_mixed_sufficient_and_unavailable_excludes_the_unavailable_ones() -> None:
    observations = [
        make_observation(f"good{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ] + [_unavailable_obs("bad1", date(2026, 1, 20)), _unavailable_obs("bad2", date(2026, 1, 21))]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.ESTABLISHED
    assert baseline.n_sessions == 6
    assert set(baseline.excluded_observation_ids) == {"bad1", "bad2"}
    assert baseline.exclusion_reasons["bad1"] == "gated"


def test_limited_quality_observations_still_contribute_a_value() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i, quality="limited")
        for i in range(6)
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.ESTABLISHED
    assert baseline.n_sessions == 6
    assert baseline.center is not None


def test_insufficient_quality_is_excluded_with_its_own_reason() -> None:
    observations = [_insufficient_obs("s1", date(2026, 1, 10))]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.INSUFFICIENT_DATA
    assert baseline.exclusion_reasons["s1"] == "not enough trials"


# --- MISSINGNESS --------------------------------------------------------------


def test_unavailable_observation_never_becomes_zero_in_the_estimate() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=10.0) for i in range(6)
    ] + [_unavailable_obs("gap", date(2026, 1, 20))]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    # If the gap were silently treated as 0.0, the median would drop
    # sharply; it must not.
    assert baseline.center == 10.0


def test_unavailable_metric_is_never_perfect_or_worst_score() -> None:
    baseline = estimate_baseline("p1", _METRIC, [_unavailable_obs("s1", date(2026, 1, 10))], _AS_OF)
    assert baseline.center is None


# --- PROVENANCE ----------------------------------------------------------------


def test_contributing_observation_ids_match_the_usable_sessions() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert set(baseline.contributing_observation_ids) == {f"s{i}" for i in range(6)}


def test_period_bounds_reflect_the_actual_contributing_dates() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.period_start == date(2026, 1, 10)
    assert baseline.period_end == date(2026, 1, 15)
