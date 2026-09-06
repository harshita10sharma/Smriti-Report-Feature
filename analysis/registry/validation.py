"""Registry-consistency validation (master spec S22 Phase 2 acceptance
criteria).

Runs structural checks across the game and metric registries that no
single pydantic model can express alone (e.g. "every metric's game_id
must reference an actually-registered game"). Raises ``RegistryError``
- not a generic exception - so callers can distinguish "the registry
itself is broken" from any other failure.
"""

from __future__ import annotations

from analysis.errors import RegistryError
from analysis.models.enums import GameId
from analysis.registry.games import GameDefinition
from analysis.registry.metrics import RegisteredMetric


def validate_registry(
    games: tuple[GameDefinition, ...], metrics: tuple[RegisteredMetric, ...]
) -> None:
    """Validate the full game/metric registry, raising on any violation.

    Collects every problem before raising (rather than stopping at the
    first) so a single failed validation run reports everything wrong
    at once.
    """
    problems: list[str] = []
    problems.extend(_check_all_nine_games_present(games))
    problems.extend(_check_no_duplicate_game_ids(games))
    problems.extend(_check_metrics_reference_registered_games(games, metrics))
    problems.extend(_check_no_duplicate_metric_ids(metrics))
    problems.extend(_check_metric_fields_are_representable(games, metrics))

    if problems:
        raise RegistryError(
            f"registry validation failed with {len(problems)} problem(s):\n"
            + "\n".join(f"  - {problem}" for problem in problems)
        )


def _check_all_nine_games_present(games: tuple[GameDefinition, ...]) -> list[str]:
    registered = {game.game_id for game in games}
    missing = set(GameId) - registered
    if missing:
        return [f"missing games in registry: {sorted(g.value for g in missing)}"]
    if len(registered) != 9:
        return [f"expected exactly 9 canonical games, found {len(registered)}"]
    return []


def _check_no_duplicate_game_ids(games: tuple[GameDefinition, ...]) -> list[str]:
    seen: set[GameId] = set()
    problems: list[str] = []
    for game in games:
        if game.game_id in seen:
            problems.append(f"duplicate game_id: {game.game_id.value}")
        seen.add(game.game_id)
    return problems


def _check_no_duplicate_metric_ids(metrics: tuple[RegisteredMetric, ...]) -> list[str]:
    seen: set[str] = set()
    problems: list[str] = []
    for metric in metrics:
        if metric.metric_id in seen:
            problems.append(f"duplicate metric_id: {metric.metric_id}")
        seen.add(metric.metric_id)
    return problems


def _check_metrics_reference_registered_games(
    games: tuple[GameDefinition, ...], metrics: tuple[RegisteredMetric, ...]
) -> list[str]:
    registered = {game.game_id for game in games}
    return [
        f"metric {metric.metric_id!r} references unregistered game "
        f"{metric.game_id.value!r}"
        for metric in metrics
        if metric.game_id not in registered
    ]


def _check_metric_fields_are_representable(
    games: tuple[GameDefinition, ...], metrics: tuple[RegisteredMetric, ...]
) -> list[str]:
    """Every non-jsonb required field of a metric must be a field the
    owning game actually declares (required or optional)."""
    games_by_id = {game.game_id: game for game in games}
    problems: list[str] = []
    for metric in metrics:
        game = games_by_id.get(metric.game_id)
        if game is None:
            continue  # already reported by _check_metrics_reference_registered_games
        declared = set(game.required_event_fields) | set(game.optional_event_fields)
        for field in metric.required_fields:
            if field.startswith("metrics."):
                continue  # proposed jsonb key, not a declared event field
            if field not in declared:
                problems.append(
                    f"metric {metric.metric_id!r} requires field {field!r} "
                    f"that game {metric.game_id.value!r} does not declare "
                    "as a required or optional event field"
                )
    return problems
