"""Phase 2 acceptance-criteria tests (master spec Phase 2).

Exercises the real, registered GAMES/METRICS data directly - not just
the validator logic in isolation (see test_validation.py for that) -
so a future edit to the registry data itself is checked against every
criterion the specification names.
"""

import importlib

from analysis.models.enums import GameId, TelemetrySource
from analysis.registry import GAME_REGISTRY, GAMES, METRIC_REGISTRY, METRICS, REGISTRY_VERSION
from analysis.registry.validation import validate_registry


def test_all_nine_canonical_games_exist() -> None:
    assert {game.game_id for game in GAMES} == set(GameId)
    assert len(GAMES) == 9


def test_no_duplicate_game_ids() -> None:
    ids = [game.game_id for game in GAMES]
    assert len(ids) == len(set(ids))


def test_every_game_has_a_primary_domain() -> None:
    for game in GAMES:
        assert game.primary_domain is not None


def test_every_metric_belongs_to_a_registered_game() -> None:
    registered_game_ids = {game.game_id for game in GAMES}
    for metric in METRICS:
        assert metric.game_id in registered_game_ids


def test_every_metric_has_directionality() -> None:
    for metric in METRICS:
        assert metric.direction is not None


def test_every_metric_has_a_valid_aggregation_rule() -> None:
    for metric in METRICS:
        assert metric.aggregation is not None


def test_no_duplicate_metric_ids() -> None:
    ids = [metric.metric_id for metric in METRICS]
    assert len(ids) == len(set(ids))


def test_canonical_metric_inventory_has_34_deliberately_registered_metrics() -> None:
    assert len(METRICS) == 34


def test_phase_four_semantic_gaps_remain_jsonb_gated() -> None:
    metric_ids = {
        "sort_harvest_trials_to_criterion",
        "trace_path_completion_ms",
        "name_harvest_items_named",
        "sounds_home_hit_rate",
        "sounds_home_miss_rate",
        "sounds_home_false_alarm_rate",
        "sounds_home_block_hit_rate_decline",
        "sounds_home_block_rt_decline",
    }
    for metric_id in metric_ids:
        assert METRIC_REGISTRY[metric_id].telemetry_source is (
            TelemetrySource.METRICS_JSONB_UNVERIFIED
        )


def test_every_metric_required_field_is_representable() -> None:
    # validate_registry() itself performs this check across every
    # metric; a passing call is the assertion.
    validate_registry(GAMES, METRICS)


def test_game_and_metric_registry_dicts_match_tuples() -> None:
    assert set(GAME_REGISTRY) == {game.game_id for game in GAMES}
    assert set(METRIC_REGISTRY) == {metric.metric_id for metric in METRICS}


def test_every_game_has_at_least_one_registered_metric() -> None:
    games_with_metrics = {metric.game_id for metric in METRICS}
    assert games_with_metrics == set(GameId)


def test_registry_version_is_stable_across_reimport() -> None:
    import analysis.registry as registry_module

    reimported = importlib.reload(registry_module)
    assert reimported.REGISTRY_VERSION == REGISTRY_VERSION
    assert isinstance(REGISTRY_VERSION, str) and REGISTRY_VERSION != ""
