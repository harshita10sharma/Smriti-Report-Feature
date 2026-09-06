import pytest

from analysis.errors import RegistryError
from analysis.models.enums import (
    AggregationMethod,
    Direction,
    Domain,
    GameId,
    MetricType,
    TelemetrySource,
)
from analysis.registry.game_registry import GAMES
from analysis.registry.games import GameDefinition
from analysis.registry.metric_registry import METRICS
from analysis.registry.metrics import RegisteredMetric
from analysis.registry.validation import validate_registry


def test_real_registry_passes_validation() -> None:
    validate_registry(GAMES, METRICS)  # must not raise


def test_missing_game_is_rejected() -> None:
    incomplete_games = tuple(g for g in GAMES if g.game_id != GameId.SOUNDS_OF_HOME)
    with pytest.raises(RegistryError, match="missing games"):
        validate_registry(incomplete_games, METRICS)


def test_duplicate_game_id_is_rejected() -> None:
    duplicated_games = GAMES + (GAMES[0],)
    with pytest.raises(RegistryError, match="duplicate game_id"):
        validate_registry(duplicated_games, METRICS)


def test_duplicate_metric_id_is_rejected() -> None:
    duplicated_metrics = METRICS + (METRICS[0],)
    with pytest.raises(RegistryError, match="duplicate metric_id"):
        validate_registry(GAMES, duplicated_metrics)


def test_metric_referencing_unregistered_game_is_rejected() -> None:
    orphan_game_games = tuple(g for g in GAMES if g.game_id != GameId.MY_DAY)
    my_day_metrics = tuple(m for m in METRICS if m.game_id == GameId.MY_DAY)
    assert my_day_metrics, "fixture assumption: My Day has at least one metric"
    with pytest.raises(RegistryError, match="unregistered game"):
        validate_registry(orphan_game_games, METRICS)


def test_metric_requiring_undeclared_field_is_rejected() -> None:
    minimal_game = GameDefinition(
        game_id=GameId.MY_DAY,
        display_name="My Day",
        instrument="Orientation-task analogue",
        primary_domain=Domain.MEMORY,
        constructs=("temporal orientation",),
        required_event_fields=("patient_id", "session_id", "game_id", "domain", "ts"),
    )
    other_games = tuple(g for g in GAMES if g.game_id != GameId.MY_DAY) + (minimal_game,)
    bad_metric = RegisteredMetric(
        metric_id="my_day_orientation_accuracy_bad",
        display_name="Orientation accuracy",
        description="x",
        unit="proportion",
        direction=Direction.HIGHER_IS_BETTER,
        metric_type=MetricType.PERFORMANCE,
        domain=Domain.MEMORY,
        game_id=GameId.MY_DAY,
        aggregation=AggregationMethod.RATE,
        telemetry_source=TelemetrySource.VERIFIED_COLUMN,
        required_fields=("correct",),  # minimal_game does not declare "correct"
        verification_note="x",
    )
    with pytest.raises(RegistryError, match="does not declare"):
        validate_registry(other_games, (bad_metric,))
