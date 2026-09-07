from collections.abc import Sequence

from analysis.games.trace_path import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "trace_the_path"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_completion_is_unavailable_without_a_verified_completed_attempt_marker() -> None:
    trials = [
        make_trial(game_id=_GAME, response_time_ms=1000),
        make_trial(game_id=_GAME, response_time_ms=2000),
        make_trial(game_id=_GAME, response_time_ms=3000),
    ]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["trace_path_completion_ms"]
    assert obs.value is None
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert "metrics.attempt_completed" in (obs.unavailable_reason or "")


def test_incomplete_attempt_and_motor_metrics_are_all_unavailable() -> None:
    trials = [make_trial(game_id=_GAME, response_time_ms=None)]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    for metric_id in (
        "trace_path_completion_ms",
        "trace_path_stroke_velocity",
        "trace_path_lifts",
        "trace_path_jitter",
        "trace_path_b_minus_a_ms",
    ):
        assert by_id[metric_id].quality == QualityStatus.UNAVAILABLE
        assert by_id[metric_id].value is None


def test_unverified_variant_payload_never_enables_an_a_minus_b_comparison() -> None:
    trials = [
        make_trial(
            game_id=_GAME,
            response_time_ms=1000,
            metrics={"attempt_completed": True, "variant": "a"},
        ),
        make_trial(
            game_id=_GAME,
            response_time_ms=2000,
            metrics={"attempt_completed": True, "variant": "b"},
        ),
    ]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["trace_path_b_minus_a_ms"]
    assert obs.value is None
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert "metrics.variant" in (obs.unavailable_reason or "")
