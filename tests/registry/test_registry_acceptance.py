"""Phase 2 acceptance-criteria tests (master spec Phase 2).

Exercises the real, registered GAMES/METRICS data directly - not just
the validator logic in isolation (see test_validation.py for that) -
so a future edit to the registry data itself is checked against every
criterion the specification names.
"""

from analysis.models.enums import GameId
from analysis.registry import GAME_REGISTRY, GAMES, METRIC_REGISTRY, METRICS
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
