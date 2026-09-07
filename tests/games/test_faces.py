from analysis.games.faces import analyze
from analysis.models.enums import QualityStatus
from tests.fixtures.trial_fixtures import make_trial

_GAME = "faces_of_my_family"


def test_all_progression_stage_metrics_are_unavailable() -> None:
    trials = [make_trial(game_id=_GAME, correct=True)]
    result = analyze("p1", "s1", 1, trials)
    gated_ids = {
        "faces_recognition_accuracy",
        "faces_naming_accuracy",
        "faces_relationship_accuracy",
        "faces_last_contact_recall_accuracy",
    }
    by_id = {o.metric_id: o for o in result.observations}
    for metric_id in gated_ids:
        assert by_id[metric_id].value is None
        assert by_id[metric_id].quality == QualityStatus.UNAVAILABLE
        assert by_id[metric_id].unavailable_reason is not None


def test_semantic_and_random_error_rates_computed_from_incorrect_trials() -> None:
    trials = [
        make_trial(game_id=_GAME, correct=False, error_class="semantic"),
        make_trial(game_id=_GAME, correct=False, error_class="random"),
        make_trial(game_id=_GAME, correct=True, error_class=None),
    ]
    result = analyze("p1", "s1", 1, trials)
    by_id = {o.metric_id: o for o in result.observations}
    assert by_id["faces_semantic_error_rate"].value == 0.5
    assert by_id["faces_random_error_rate"].value == 0.5


def test_no_incorrect_trials_makes_error_rates_unavailable() -> None:
    trials = [make_trial(game_id=_GAME, correct=True)]
    result = analyze("p1", "s1", 1, trials)
    by_id = {o.metric_id: o for o in result.observations}
    assert by_id["faces_semantic_error_rate"].quality == QualityStatus.UNAVAILABLE


def test_result_reports_correct_trial_count_and_game_id() -> None:
    trials = [make_trial(game_id=_GAME), make_trial(game_id=_GAME)]
    result = analyze("p1", "s1", 1, trials)
    assert result.trial_count == 2
    assert result.game_id.value == _GAME
    assert result.patient_id == "p1"
    assert result.session_id == "s1"
