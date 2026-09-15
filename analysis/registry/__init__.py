"""The canonical game -> metric -> domain registry.

This package is the single source of truth for game analytics (master
spec S22). No other module should hard-code a game's domain mapping,
metric list, or telemetry requirements - it must look them up here.

Validation runs at import time: if the registry data is ever
internally inconsistent (a metric referencing an unregistered game, a
duplicate ID, a required field the owning game never declares), this
import raises ``RegistryError`` immediately rather than letting the
inconsistency surface later as a confusing downstream failure.
"""

from __future__ import annotations

from analysis.models.enums import Domain, GameId
from analysis.registry.game_registry import GAME_REGISTRY, GAMES
from analysis.registry.games import GameDefinition
from analysis.registry.metric_registry import METRIC_REGISTRY, METRICS
from analysis.registry.metrics import RegisteredMetric
from analysis.registry.validation import validate_registry
from analysis.versioning import REGISTRY_VERSION

validate_registry(GAMES, METRICS)


def metrics_for_game(game_id: GameId) -> tuple[RegisteredMetric, ...]:
    """Return every registered metric for one game, in registration order."""
    return tuple(metric for metric in METRICS if metric.game_id == game_id)


def metrics_for_domain(domain: Domain) -> tuple[RegisteredMetric, ...]:
    """Return every registered metric assigned to one cognitive domain,
    in registration order.

    This is the single source of truth for which metrics contribute to
    a domain - the domain-estimation engine must call this rather than
    hard-coding a second game/metric-to-domain mapping.
    """
    return tuple(metric for metric in METRICS if metric.domain == domain)


__all__ = [
    "GAMES",
    "GAME_REGISTRY",
    "METRICS",
    "METRIC_REGISTRY",
    "REGISTRY_VERSION",
    "GameDefinition",
    "RegisteredMetric",
    "metrics_for_game",
    "metrics_for_domain",
]
