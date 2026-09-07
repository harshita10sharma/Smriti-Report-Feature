from collections.abc import Sequence

from analysis.games.trace_path import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "trace_the_path"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_completion_ms_is_median_response_time() -> None:
    trials = [
        make_trial(game_id=_GAME, response_time_ms=1000),
        make_trial(game_id=_GAME, response_time_ms=2000),
        make_trial(game_id=_GAME, response_time_ms=3000),
    ]
    result = analyze("p1", "s1", 1, trials)
    assert _by_id(result.observations)["trace_path_completion_ms"].value == 2000.0


def test_gated_metrics_are_all_unavailable() -> None:
    trials = [make_trial(game_id=_GAME, response_time_ms=1000)]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    for metric_id in (
        "trace_path_stroke_velocity",
        "trace_path_lifts",
        "trace_path_jitter",
        "trace_path_b_minus_a_ms",
    ):
        assert by_id[metric_id].quality == QualityStatus.UNAVAILABLE
        assert by_id[metric_id].value is None
