"""Metric metadata and observations.

``MetricDefinition`` is registry metadata: it describes what a metric
means and how it may be used, but holds no data. ``MetricObservation``
is one computed value for one session/patient. Keeping these separate
lets many observations reference one definition without duplicating
its metadata (master spec S77).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from analysis.models.enums import Direction, Domain, MetricType, QualityStatus


class MetricDefinition(BaseModel):
    """Registry metadata for a single metric.

    ``valid_range`` is ``(min, max)`` inclusive, or ``None`` if the
    metric is unbounded or its range is not yet known. ``source_games``
    lists the raw ``game_id`` string(s) (matching what the telemetry
    adapter maps onto a canonical ``GameId``) that can produce this
    metric - kept as ``str`` rather than ``GameId`` here because a
    metric definition may need to reference a game before its raw ID
    has been reconciled with the canonical enum.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    display_name: str
    description: str
    unit: str
    direction: Direction
    metric_type: MetricType
    domain: Domain
    source_games: tuple[str, ...]
    valid_range: tuple[float, float] | None = None
    minimum_observations: int = 1
    supports_practice_effect_correction: bool = False
    supports_baseline_normalization: bool = True
    supports_change_detection: bool = True


class MetricObservation(BaseModel):
    """One computed value of one metric, for one session.

    ``value`` is ``None`` whenever ``quality`` is
    ``QualityStatus.UNAVAILABLE`` - a missing metric must be
    represented explicitly, never as a fabricated number (master spec
    S4, S61). ``unavailable_reason`` is required whenever ``value`` is
    ``None`` so the reason is always traceable, not just implied.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    patient_id: str
    session_id: str
    event_id: str | None
    game_id: str
    value: float | None
    quality: QualityStatus
    unavailable_reason: str | None
    ts: int

    def model_post_init(self, __context: object) -> None:
        if self.value is None and self.unavailable_reason is None:
            raise ValueError(
                "unavailable_reason is required whenever value is None "
                f"(metric_id={self.metric_id!r}, session_id={self.session_id!r})"
            )
