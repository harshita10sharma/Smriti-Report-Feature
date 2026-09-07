from collections.abc import Sequence

from analysis.games.lamps import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "lamps_of_the_festival"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_sequence_and_item_error_rates() -> None:
    trials = [
        make_trial(game_id=_GAME, correct=False, error_class="sequence_error"),
        make_trial(game_id=_GAME, correct=False, error_class="item_error"),
        make_trial(game_id=_GAME, correct=True, error_class=None),
    ]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    assert by_id["lamps_sequence_error_rate"].value == 0.5
    assert by_id["lamps_item_error_rate"].value == 0.5


def test_span_metrics_are_gated() -> None:
    trials = [make_trial(game_id=_GAME, correct=True)]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    assert by_id["lamps_forward_span_achieved"].quality == QualityStatus.UNAVAILABLE
    assert by_id["lamps_backward_span_achieved"].quality == QualityStatus.UNAVAILABLE
