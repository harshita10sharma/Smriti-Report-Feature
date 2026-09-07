from collections.abc import Sequence

from analysis.games.sort_harvest import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "sort_the_harvest"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_perseverative_error_rate() -> None:
    trials = [
        make_trial(game_id=_GAME, correct=False, error_class="perseverative"),
        make_trial(game_id=_GAME, correct=True, error_class=None),
    ]
    result = analyze("p1", "s1", 1, trials)
    assert _by_id(result.observations)["sort_harvest_perseverative_error_rate"].value == 0.5


def test_switch_cost_is_always_unavailable() -> None:
    trials = [make_trial(game_id=_GAME, correct=True)]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["sort_harvest_switch_cost_ms"]
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert obs.value is None


def test_trials_to_criterion_reached() -> None:
    trials = [
        make_trial(game_id=_GAME, trial_index=0, correct=False),
        make_trial(game_id=_GAME, trial_index=1, correct=True),
        make_trial(game_id=_GAME, trial_index=2, correct=True),
        make_trial(game_id=_GAME, trial_index=3, correct=True),
    ]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["sort_harvest_trials_to_criterion"]
    assert obs.value == 4.0
    assert obs.quality == QualityStatus.SUFFICIENT


def test_trials_to_criterion_never_reached() -> None:
    trials = [make_trial(game_id=_GAME, trial_index=i, correct=False) for i in range(5)]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["sort_harvest_trials_to_criterion"]
    assert obs.value is None
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert "not reached" in (obs.unavailable_reason or "")


def test_trials_to_criterion_insufficient_trials() -> None:
    trials = [make_trial(game_id=_GAME, trial_index=0, correct=True)]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["sort_harvest_trials_to_criterion"]
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert "minimum_observations" in (obs.unavailable_reason or "")


def test_trials_to_criterion_ignores_trials_without_trial_index_or_correct() -> None:
    trials = [
        make_trial(game_id=_GAME, trial_index=None, correct=True),
        make_trial(game_id=_GAME, trial_index=0, correct=None),
        make_trial(game_id=_GAME, trial_index=1, correct=True),
        make_trial(game_id=_GAME, trial_index=2, correct=True),
        make_trial(game_id=_GAME, trial_index=3, correct=True),
    ]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["sort_harvest_trials_to_criterion"]
    # only 3 trials are eligible (indices 1,2,3); criterion reached at the
    # 3rd eligible trial
    assert obs.value == 3.0
