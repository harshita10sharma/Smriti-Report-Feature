from collections.abc import Sequence

from analysis.games.name_harvest import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "name_the_harvest"


def _by_id(observations: Sequence[MetricObservation]) -> dict[str, MetricObservation]:
    return {o.metric_id: o for o in observations}


def test_items_named_is_unavailable_without_verified_item_level_telemetry() -> None:
    trials = [make_trial(game_id=_GAME, correct=True) for _ in range(4)] + [
        make_trial(game_id=_GAME, correct=False)
    ]
    result = analyze("p1", "s1", 1, trials)
    obs = _by_id(result.observations)["name_harvest_items_named"]
    assert obs.value is None
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert "metrics.named_item_id" in (obs.unavailable_reason or "")


def test_clusters_and_switches_are_gated() -> None:
    trials = [make_trial(game_id=_GAME, correct=True)]
    result = analyze("p1", "s1", 1, trials)
    by_id = _by_id(result.observations)
    assert by_id["name_harvest_clusters"].quality == QualityStatus.UNAVAILABLE
    assert by_id["name_harvest_switches"].quality == QualityStatus.UNAVAILABLE


def test_audio_path_is_not_a_registered_metric() -> None:
    result = analyze("p1", "s1", 1, [make_trial(game_id=_GAME)])
    assert "audio_path" not in {o.metric_id for o in result.observations}


def test_unverified_named_item_payload_is_not_silently_interpreted() -> None:
    result = analyze(
        "p1",
        "s1",
        1,
        [make_trial(game_id=_GAME, correct=True, metrics={"named_item_id": "mango"})],
    )
    obs = _by_id(result.observations)["name_harvest_items_named"]
    assert obs.value is None
    assert obs.quality == QualityStatus.UNAVAILABLE
