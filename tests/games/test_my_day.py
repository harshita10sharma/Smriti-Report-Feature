from collections.abc import Sequence

from analysis.games.my_day import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "my_day"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_orientation_accuracy_from_correct_column() -> None:
    trials = [
        make_trial(game_id=_GAME, correct=True),
        make_trial(game_id=_GAME, correct=True),
        make_trial(game_id=_GAME, correct=False),
        make_trial(game_id=_GAME, correct=True),
    ]
    result = analyze("p1", "s1", 1, trials)
    assert _by_id(result.observations)["my_day_orientation_accuracy"].value == 0.75


def test_no_trials_is_unavailable() -> None:
    result = analyze("p1", "s1", 1, [])
    obs = _by_id(result.observations)["my_day_orientation_accuracy"]
    assert obs.quality == QualityStatus.UNAVAILABLE
