from collections.abc import Sequence

from analysis.games.weaving import analyze
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "weaving_patterns"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_all_four_error_classes_computed_independently() -> None:
    trials = [
        make_trial(game_id=_GAME, correct=False, error_class="mirror"),
        make_trial(game_id=_GAME, correct=False, error_class="rotation"),
        make_trial(game_id=_GAME, correct=False, error_class="detail"),
        make_trial(game_id=_GAME, correct=False, error_class="random"),
    ]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    assert by_id["weaving_mirror_error_rate"].value == 0.25
    assert by_id["weaving_rotation_error_rate"].value == 0.25
    assert by_id["weaving_detail_error_rate"].value == 0.25
    assert by_id["weaving_random_error_rate"].value == 0.25


def test_no_errors_gives_zero_rates() -> None:
    trials = [make_trial(game_id=_GAME, correct=False, error_class="mirror")]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    assert by_id["weaving_rotation_error_rate"].value == 0.0
