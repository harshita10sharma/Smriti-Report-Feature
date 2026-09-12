"""RegisteredMetric: registry metadata for one metric of one game.

This is distinct from ``analysis.models.metrics.MetricDefinition``:
that type is the generic shape any metric definition takes, while
``RegisteredMetric`` is the registry's own record, additionally
tracking *how confident this project is* that the metric's required
telemetry actually exists (``telemetry_source`` /
``required_fields``) - see ``analysis.models.enums.TelemetrySource``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import (
    AggregationMethod,
    Direction,
    Domain,
    GameId,
    MetricType,
    TelemetrySource,
)


class RegisteredMetric(BaseModel):
    """One metric definition as recorded in the canonical registry.

    ``required_fields`` entries are either a verified column name
    (e.g. ``"correct"``) or, when ``telemetry_source`` is
    ``METRICS_JSONB_UNVERIFIED``, a proposed jsonb key written as
    ``"metrics.<key>"`` - proposed, not confirmed, per
    REPORT_READINESS_AUDIT.md S4. ``verification_note`` must always
    explain the ``telemetry_source`` classification in plain language
    so a reader never has to infer it.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    display_name: str
    description: str
    unit: str
    direction: Direction
    metric_type: MetricType
    domain: Domain
    game_id: GameId
    aggregation: AggregationMethod
    telemetry_source: TelemetrySource
    required_fields: tuple[str, ...]
    verification_note: str
    minimum_observations: int = 1
    supports_practice_effect_correction: bool = False
    supports_baseline_normalization: bool = True
    supports_change_detection: bool = True
    #: (min, max) inclusive bounds a raw contributing value must fall
    #: within to be usable, or None if no defensible bound exists yet.
    #: Populated only where the metric's own semantics make a bound
    #: unambiguous (e.g. a proportion is always [0.0, 1.0]) - never
    #: invented to make validation "do something" (master spec S22/S49).
    valid_range: tuple[float, float] | None = None

    @model_validator(mode="after")
    def _valid_range_is_ordered(self) -> RegisteredMetric:
        if self.valid_range is not None and self.valid_range[0] > self.valid_range[1]:
            raise ValueError(
                f"{self.metric_id}: valid_range {self.valid_range} has min > max"
            )
        return self

    @model_validator(mode="after")
    def _jsonb_fields_are_marked_as_such(self) -> RegisteredMetric:
        jsonb_fields = [f for f in self.required_fields if f.startswith("metrics.")]
        if jsonb_fields and self.telemetry_source != TelemetrySource.METRICS_JSONB_UNVERIFIED:
            raise ValueError(
                f"{self.metric_id}: required_fields reference metrics jsonb "
                f"keys {jsonb_fields} but telemetry_source is "
                f"{self.telemetry_source.value!r}, not METRICS_JSONB_UNVERIFIED"
            )
        if self.telemetry_source == TelemetrySource.METRICS_JSONB_UNVERIFIED and not jsonb_fields:
            raise ValueError(
                f"{self.metric_id}: telemetry_source is "
                "METRICS_JSONB_UNVERIFIED but no required_fields entry "
                "starts with 'metrics.'"
            )
        return self

    @model_validator(mode="after")
    def _has_at_least_one_required_field(self) -> RegisteredMetric:
        if not self.required_fields:
            raise ValueError(f"{self.metric_id}: required_fields must not be empty")
        return self
