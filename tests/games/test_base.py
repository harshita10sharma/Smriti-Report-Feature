import pytest

from analysis.games.base import (
    compute_count,
    compute_dispersion,
    compute_rate,
    gated_unavailable,
    observation,
)
from analysis.models.enums import QualityStatus, TelemetrySource
from analysis.registry import METRIC_REGISTRY
from tests.fixtures.trial_fixtures import make_trial

_VERIFIED_RATE_METRIC = METRIC_REGISTRY["sort_harvest_perseverative_error_rate"]
_GATED_METRIC = METRIC_REGISTRY["sort_harvest_switch_cost_ms"]
_DISPERSION_METRIC = METRIC_REGISTRY["sounds_home_rt_sd"]
_COUNT_METRIC = _VERIFIED_RATE_METRIC


def test_gated_unavailable_never_exposes_a_value() -> None:
    result = gated_unavailable(_GATED_METRIC, patient_id="p1", session_id="s1", ts=1)
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE
    assert result.unavailable_reason is not None
    assert "telemetry_source=metrics_jsonb_unverified" in result.unavailable_reason


def test_compute_rate_on_verified_metric() -> None:
    trials = [
        make_trial(correct=False, error_class="perseverative"),
        make_trial(correct=True, error_class=None),
    ]
    result = compute_rate(
        _VERIFIED_RATE_METRIC,
        patient_id="p1",
        session_id="s1",
        ts=2,
        trials=trials,
        is_eligible=lambda t: t.correct is not None,
        is_positive=lambda t: t.error_class == "perseverative",
    )
    assert result.value == 0.5
    assert result.quality == QualityStatus.SUFFICIENT


def test_compute_rate_raises_for_a_gated_metric() -> None:
    with pytest.raises(AssertionError, match="attempted to compute"):
        compute_rate(
            _GATED_METRIC,
            patient_id="p1",
            session_id="s1",
            ts=1,
            trials=[make_trial()],
            is_eligible=lambda t: True,
            is_positive=lambda t: True,
        )


def test_compute_rate_returns_unavailable_below_minimum_observations() -> None:
    metric = _VERIFIED_RATE_METRIC.model_copy(update={"minimum_observations": 5})
    result = compute_rate(
        metric,
        patient_id="p1",
        session_id="s1",
        ts=1,
        trials=[make_trial(correct=True)],
        is_eligible=lambda t: t.correct is not None,
        is_positive=lambda t: False,
    )
    assert result.value is None
    assert result.quality == QualityStatus.UNAVAILABLE
    assert "minimum_observations=5" in (result.unavailable_reason or "")


def test_compute_dispersion_computes_stddev() -> None:
    trials = [
        make_trial(response_time_ms=100),
        make_trial(response_time_ms=200),
        make_trial(response_time_ms=300),
    ]
    result = compute_dispersion(
        _DISPERSION_METRIC,
        patient_id="p1",
        session_id="s1",
        ts=3,
        trials=trials,
        extractor=lambda t: float(t.response_time_ms) if t.response_time_ms is not None else None,
    )
    assert result.value is not None
    assert result.value > 0


def test_compute_dispersion_skips_trials_missing_the_field() -> None:
    trials = [make_trial(response_time_ms=None), make_trial(response_time_ms=100)]
    metric = _DISPERSION_METRIC.model_copy(update={"minimum_observations": 2})
    result = compute_dispersion(
        metric,
        patient_id="p1",
        session_id="s1",
        ts=1,
        trials=trials,
        extractor=lambda t: float(t.response_time_ms) if t.response_time_ms is not None else None,
    )
    assert result.quality == QualityStatus.UNAVAILABLE


def test_compute_count() -> None:
    trials = [make_trial(correct=True), make_trial(correct=True), make_trial(correct=False)]
    result = compute_count(
        _COUNT_METRIC,
        patient_id="p1",
        session_id="s1",
        ts=1,
        trials=trials,
        is_eligible=lambda t: bool(t.correct),
    )
    assert result.value == 2.0


def test_observation_helper_sets_expected_fields() -> None:
    result = observation(
        _VERIFIED_RATE_METRIC, patient_id="p1", session_id="s1", ts=5, value=0.25
    )
    assert result.value == 0.25
    assert result.quality == QualityStatus.SUFFICIENT
    assert result.unavailable_reason is None
    assert result.ts == 5


def test_every_metric_gate_is_one_of_two_kinds() -> None:
    # sanity check that the two metrics used as fixtures above actually
    # represent the two paths this module exercises.
    assert _VERIFIED_RATE_METRIC.telemetry_source == TelemetrySource.VERIFIED_COLUMN
    assert _GATED_METRIC.telemetry_source == TelemetrySource.METRICS_JSONB_UNVERIFIED
