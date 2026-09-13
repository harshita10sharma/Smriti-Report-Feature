"""Typed inputs and outputs for the Phase 5 aggregation engine.

``RawObservation`` is deliberately not ``Trial`` - it decouples this
package from game-specific telemetry shapes so the same aggregation
logic can later combine values from any source (e.g. one
MetricObservation per session, across many sessions), not just trials
within a single session.
"""

from __future__ import annotations

import math

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import AggregationMethod, GameId, QualityStatus


class RawObservation(BaseModel):
    """One contributing data point to be aggregated.

    ``value`` is ``None`` when the source simply did not supply a
    value (missing) - this is different from a present-but-invalid
    value, which the aggregator itself detects and excludes (see
    ``analysis.aggregation.engine``).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    ts: int
    value: float | None

    @model_validator(mode="after")
    def _value_is_finite_when_present(self) -> RawObservation:
        if self.value is not None and not math.isfinite(self.value):
            raise ValueError(
                f"RawObservation(source_id={self.source_id!r}).value must be "
                f"finite when present, got {self.value}"
            )
        return self


class ExcludedObservation(BaseModel):
    """One raw observation that did not contribute to the aggregate,
    and why - so aggregation never silently discards a data point."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str
    reason_code: str
    reason_message: str


class AggregationResult(BaseModel):
    """The full, provenance-preserving output of one aggregation.

    Distinct from ``analysis.models.metrics.MetricObservation``
    (Phase 4's simpler per-session shape): this type additionally
    preserves exactly which observations contributed, which were
    excluded and why, and how many were missing versus invalid -
    detail Phase 4's model has no fields for.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    patient_id: str
    game_id: GameId
    aggregation: AggregationMethod
    value: float | None
    quality: QualityStatus
    reason: str | None
    valid_count: int
    missing_count: int
    excluded: tuple[ExcludedObservation, ...]
    source_ids: tuple[str, ...]
    ts_range: tuple[int, int] | None

    @model_validator(mode="after")
    def _value_requires_no_reason_and_vice_versa(self) -> AggregationResult:
        if self.value is None and self.reason is None:
            raise ValueError(
                "reason is required whenever value is None "
                f"(metric_id={self.metric_id!r}, patient_id={self.patient_id!r})"
            )
        return self

    @model_validator(mode="after")
    def _counts_are_non_negative(self) -> AggregationResult:
        if self.valid_count < 0 or self.missing_count < 0:
            raise ValueError(
                f"{self.metric_id}: valid_count and missing_count must not be negative "
                f"(got valid_count={self.valid_count}, missing_count={self.missing_count})"
            )
        return self

    @model_validator(mode="after")
    def _ts_range_is_ordered(self) -> AggregationResult:
        if self.ts_range is not None and self.ts_range[0] > self.ts_range[1]:
            raise ValueError(f"{self.metric_id}: ts_range {self.ts_range} has min > max")
        return self
