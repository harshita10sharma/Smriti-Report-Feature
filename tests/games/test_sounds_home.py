"""Regression coverage for the verified Sounds of Home telemetry boundary."""

from __future__ import annotations

import math

import pydantic
import pytest

from analysis.games.sounds_home import analyze
from analysis.models.enums import QualityStatus
from analysis.models.metrics import MetricObservation
from tests.fixtures.trial_fixtures import make_trial

_GAME = "sounds_of_home"


def _by_id(observations: tuple[MetricObservation, ...]) -> dict[str, MetricObservation]:
    return {observation.metric_id: observation for observation in observations}


def test_rt_variability_uses_only_verified_response_time_values() -> None:
    result = analyze(
        "p1",
        "s1",
        1,
        [
            make_trial(game_id=_GAME, response_time_ms=100),
            make_trial(game_id=_GAME, response_time_ms=200),
            make_trial(game_id=_GAME, response_time_ms=300),
        ],
    )

    obs = _by_id(result.observations)["sounds_home_rt_sd"]
    assert obs.quality == QualityStatus.SUFFICIENT
    assert obs.value == pytest.approx(math.sqrt(20_000 / 3))


def test_target_dependent_rates_are_unavailable_without_a_verified_target_contract() -> None:
    result = analyze(
        "p1",
        "s1",
        1,
        [
            make_trial(game_id=_GAME, correct=True),
            make_trial(game_id=_GAME, correct=False, error_class="miss"),
            make_trial(game_id=_GAME, correct=False, error_class="false_alarm"),
        ],
    )

    by_id = _by_id(result.observations)
    for metric_id in (
        "sounds_home_hit_rate",
        "sounds_home_miss_rate",
        "sounds_home_false_alarm_rate",
    ):
        assert by_id[metric_id].value is None
        assert by_id[metric_id].quality == QualityStatus.UNAVAILABLE
        assert "metrics.is_target" in (by_id[metric_id].unavailable_reason or "")


def test_block_metrics_are_not_inferred_from_timestamps_or_unverified_payloads() -> None:
    start = 1_700_000_000_000
    result = analyze(
        "p1",
        "s1",
        start,
        [
            make_trial(
                game_id=_GAME,
                correct=True,
                response_time_ms=100,
                ts=start,
                metrics={"is_target": True, "block_index": 0},
            ),
            make_trial(
                game_id=_GAME,
                correct=True,
                response_time_ms=300,
                ts=start + 60_000,
                metrics={"is_target": True, "block_index": 2},
            ),
        ],
    )

    by_id = _by_id(result.observations)
    for metric_id in ("sounds_home_block_hit_rate_decline", "sounds_home_block_rt_decline"):
        assert by_id[metric_id].value is None
        assert by_id[metric_id].quality == QualityStatus.UNAVAILABLE
        assert "metrics.block_index" in (by_id[metric_id].unavailable_reason or "")


def test_incomplete_trials_leave_rt_variability_explicitly_unavailable() -> None:
    result = analyze("p1", "s1", 1, [make_trial(game_id=_GAME, response_time_ms=None)])
    obs = _by_id(result.observations)["sounds_home_rt_sd"]
    assert obs.value is None
    assert obs.quality == QualityStatus.UNAVAILABLE
    assert "minimum_observations" in (obs.unavailable_reason or "")


def test_malformed_trial_is_rejected_before_it_reaches_the_analyzer() -> None:
    with pytest.raises(pydantic.ValidationError):
        make_trial(game_id=_GAME, response_time_ms="not-a-duration")
