from analysis.games.market_basket import analyze
from analysis.models.enums import QualityStatus
from tests.fixtures.trial_fixtures import make_trial


def test_both_span_metrics_are_unavailable() -> None:
    trials = [make_trial(game_id="market_basket", correct=True)]
    result = analyze("p1", "s1", 1, trials)
    assert len(result.observations) == 2
    for o in result.observations:
        assert o.value is None
        assert o.quality == QualityStatus.UNAVAILABLE
        assert o.unavailable_reason is not None


def test_result_carries_trial_count() -> None:
    trials = [make_trial(game_id="market_basket") for _ in range(3)]
    result = analyze("p1", "s1", 1, trials)
    assert result.trial_count == 3
