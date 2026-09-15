"""Typed inputs/outputs specific to baseline and practice-effect
assessment.

``analysis.models.baseline.Baseline`` (the estimate itself) already
exists from the project's foundation layer and is reused unchanged.
What is missing - and defined here - is the *input* shape: Phase 5's
``AggregationResult`` has no session identity or calendar date (it
represents one already-aggregated value, not a point in time), so
baseline estimation needs a small wrapper that pairs one session's
result with the identity and date the baseline engine needs to order
and window it correctly.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.aggregation.models import AggregationResult
from analysis.models.enums import QualityStatus


class BaselineObservation(BaseModel):
    """One session's aggregated metric value, as input to baseline
    estimation.

    ``session_id`` is supplied by the caller (the orchestration layer
    that ran Phase 4/5 for that session) rather than derived from
    ``result``, since ``AggregationResult`` may aggregate across
    multiple sessions and does not itself carry session identity.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    observed_on: date
    result: AggregationResult

    @property
    def is_usable(self) -> bool:
        """True when this observation has a real value to contribute
        (quality SUFFICIENT or LIMITED) - false for INSUFFICIENT or
        UNAVAILABLE, which never carry a value (master spec S16)."""
        return self.result.quality in (QualityStatus.SUFFICIENT, QualityStatus.LIMITED)


class PracticeObservationPoint(BaseModel):
    """One raw (never corrected) point in a metric's practice trajectory."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    session_id: str
    observed_on: date
    value: float


class PracticeEffectAssessment(BaseModel):
    """The practice-effect foundation for one patient/metric.

    No correction is computed here - ``raw_trajectory`` is the
    deterministic extension point a later phase can fit an actual
    learning-curve model against, once verified telemetry exists to
    justify one (e.g. confirmed item-repetition data). Today, every
    consumer of this type must treat the metric's practice effect as
    unassessed, not as "no practice effect exists."
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: str
    metric_id: str
    status: QualityStatus
    reason: str | None
    raw_trajectory: tuple[PracticeObservationPoint, ...]
    correction_applied: bool

    @model_validator(mode="after")
    def _no_correction_is_applied_yet(self) -> PracticeEffectAssessment:
        if self.correction_applied:
            raise ValueError(
                "no practice-effect correction model is implemented yet; "
                "correction_applied must remain False"
            )
        return self

    @model_validator(mode="after")
    def _status_requires_no_reason_and_vice_versa(self) -> PracticeEffectAssessment:
        if self.status in (QualityStatus.UNAVAILABLE, QualityStatus.INSUFFICIENT):
            if self.reason is None:
                raise ValueError(
                    f"reason is required when status is {self.status.value}"
                )
        return self

    @model_validator(mode="after")
    def _trajectory_is_ordered_by_date(self) -> PracticeEffectAssessment:
        dates = [point.observed_on for point in self.raw_trajectory]
        if dates != sorted(dates):
            raise ValueError("raw_trajectory must be ordered by observed_on")
        return self
