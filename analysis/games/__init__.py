"""Game-specific feature extraction (master spec S21, S76, Phase 4).

Each module here implements one game's analyzer: a pure function that
turns a session's validated ``Trial`` objects into ``MetricObservation``
values for every metric this project has registered for that game
(``analysis.registry.metrics_for_game``).

A metric the registry gates as ``METRICS_JSONB_UNVERIFIED`` or
``CROSS_TABLE_UNVERIFIED`` is always reported ``UNAVAILABLE`` here -
no analyzer reads a Trial's ``metrics`` payload at all, so it is
structurally impossible for this package to promote an unconfirmed
jsonb key to a trusted value.
"""
