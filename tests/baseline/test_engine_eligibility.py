from datetime import date

from analysis.baseline.engine import estimate_baseline, estimate_domain_baselines
from analysis.models.enums import BaselineStatus, Domain
from analysis.registry import metrics_for_domain
from tests.fixtures.baseline_fixtures import make_observation

_METRIC = "sort_harvest_perseverative_error_rate"
_AS_OF = date(2026, 1, 30)


def test_empty_evidence_is_insufficient_data() -> None:
    baseline = estimate_baseline("p1", _METRIC, [], _AS_OF)
    assert baseline.status == BaselineStatus.INSUFFICIENT_DATA
    assert baseline.center is None
    assert baseline.n_sessions == 0


def test_one_observation_is_establishing_not_established() -> None:
    observations = [make_observation("s1", date(2026, 1, 10), value=0.1)]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.ESTABLISHING
    assert baseline.center is None
    assert baseline.n_sessions == 1


def test_repeated_observations_across_enough_days_establish_baseline() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.ESTABLISHED
    assert baseline.n_sessions == 6
    assert baseline.n_days == 6
    assert baseline.center is not None
    assert baseline.variability is not None


def test_enough_sessions_but_same_day_remains_establishing() -> None:
    # 6 sessions, but all on the same calendar day - fails the
    # distinct-days requirement even though the session count is met.
    observations = [
        make_observation(f"s{i}", date(2026, 1, 15), value=0.1 * i) for i in range(6)
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.ESTABLISHING
    assert baseline.n_sessions == 6
    assert baseline.n_days == 1


def test_sparse_sessions_outside_the_window_do_not_count() -> None:
    # One observation far outside the 28-day window, one inside.
    observations = [
        make_observation("old", date(2025, 1, 1), value=0.9),
        make_observation("recent", date(2026, 1, 20), value=0.1),
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.n_sessions == 1
    assert "old" not in baseline.contributing_observation_ids
    assert baseline.status != BaselineStatus.ESTABLISHED


def test_all_insufficient_quality_observations_yield_insufficient_data() -> None:
    observations = [
        make_observation(
            f"s{i}", date(2026, 1, 10 + i), value=None,
            quality="unavailable", reason="gated", valid_count=0, source_ids=(), ts_range=None,
        )
        for i in range(6)
    ]
    baseline = estimate_baseline("p1", _METRIC, observations, _AS_OF)
    assert baseline.status == BaselineStatus.INSUFFICIENT_DATA
    assert baseline.n_sessions == 0
    assert len(baseline.excluded_observation_ids) == 6


def test_estimate_domain_baselines_covers_every_registered_metric() -> None:
    baselines = estimate_domain_baselines(Domain.EXECUTIVE, "p1", {}, _AS_OF)
    registered_ids = {m.metric_id for m in metrics_for_domain(Domain.EXECUTIVE)}
    assert set(baselines) == registered_ids


def test_estimate_domain_baselines_gates_unverified_metrics_without_data() -> None:
    baselines = estimate_domain_baselines(Domain.EXECUTIVE, "p1", {}, _AS_OF)
    # sort_harvest_switch_cost_ms is telemetry-gated - always insufficient,
    # with no observations required from the caller.
    assert baselines["sort_harvest_switch_cost_ms"].status == BaselineStatus.INSUFFICIENT_DATA


def test_estimate_domain_baselines_uses_supplied_observations_for_verified_metrics() -> None:
    observations = [
        make_observation(f"s{i}", date(2026, 1, 10 + i), value=0.1 * i) for i in range(6)
    ]
    baselines = estimate_domain_baselines(
        Domain.EXECUTIVE, "p1", {_METRIC: observations}, _AS_OF
    )
    assert baselines[_METRIC].status == BaselineStatus.ESTABLISHED
