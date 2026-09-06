"""Longitudinal trajectory and change-point shapes.

These are the output types of the trajectory-estimation and change-
detection phases (later phases); this module only establishes the
shapes so other Phase 1 foundations (Evidence, Report) can reference
them. No smoothing, trend-estimation, or detection algorithm lives
here.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import Direction, QualityStatus


class TrajectoryPoint(BaseModel):
    """One point on a metric/domain trajectory.

    Represents an existing observation period (e.g. one day), never a
    manufactured point for a period with no gameplay (master spec
    S41/S82) - a period with zero observations should simply be
    absent from the trajectory, not represented as a zero-sample
    point here.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    period_start: date
    period_end: date
    raw_value: float
    normalized_value: float | None
    smoothed_value: float | None
    sample_count: int
    quality: QualityStatus

    @model_validator(mode="after")
    def _sample_count_is_positive(self) -> TrajectoryPoint:
        if self.sample_count < 1:
            raise ValueError(
                "a TrajectoryPoint must represent at least one observation; "
                "a period with zero observations must not appear at all"
            )
        return self


class ChangePoint(BaseModel):
    """A candidate shift identified by the change detector.

    This is a *candidate* - whether it becomes report-worthy is
    decided by the separate persistence engine (master spec S85),
    hence ``persistent`` is ``None`` until that engine has evaluated
    it, not defaulted to ``True``/``False``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    changepoint_date: date
    direction: Direction
    magnitude: float
    confidence: float
    pre_change_window: tuple[date, date]
    post_change_window: tuple[date, date]
    detection_method: str
    persistent: bool | None = None

    @model_validator(mode="after")
    def _confidence_is_a_probability(self) -> ChangePoint:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(
                f"confidence must be in [0.0, 1.0], got {self.confidence}"
            )
        return self


class Trajectory(BaseModel):
    """The longitudinal trajectory of one metric for one patient."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: str
    metric_id: str
    points: tuple[TrajectoryPoint, ...]
    smoothing_method: str | None
    trend_direction: Direction | None
    quality: QualityStatus
    change_points: tuple[ChangePoint, ...] = ()

    @property
    def sample_count(self) -> int:
        return sum(point.sample_count for point in self.points)
