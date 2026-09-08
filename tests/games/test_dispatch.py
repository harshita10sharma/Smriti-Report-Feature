import pytest

from analysis.games.dispatch import analyze_game
from analysis.models.enums import GameId
from tests.fixtures.trial_fixtures import make_trial


@pytest.mark.parametrize("game_id", list(GameId))
def test_every_canonical_game_dispatches_to_a_working_analyzer(game_id: GameId) -> None:
    trials = [make_trial(game_id=game_id.value, correct=True)]
    result = analyze_game(game_id, "p1", "s1", 1, trials)
    assert result.game_id == game_id
    assert result.patient_id == "p1"
    assert result.session_id == "s1"
    assert result.trial_count == 1
    assert len(result.observations) > 0


def test_dispatch_covers_exactly_the_nine_canonical_games() -> None:
    from analysis.games.dispatch import _ANALYZERS

    assert set(_ANALYZERS) == set(GameId)
    assert len(_ANALYZERS) == 9
