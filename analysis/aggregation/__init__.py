"""Metric quality evaluation and registry-driven aggregation (Phase 5).

This package sits between game-specific feature extraction (Phase 4,
``analysis.games``, which produces one ``MetricObservation`` per
game/session) and domain estimation (Phase 6, not yet implemented).
It answers exactly one question: *can this metric's contributing raw
values be trusted, and how should they be combined per the registry's
declared aggregation method?*

It does not answer "what is this person's cognitive ability" (that is
domain estimation) and it never combines observations across the five
cognitive domains into a single score.

Every aggregation is driven by the existing ``analysis.registry``
metric metadata (``aggregation``, ``telemetry_source``,
``minimum_observations``, ``valid_range``) - this package introduces
no second registry and no per-game hard-coded logic.
"""
