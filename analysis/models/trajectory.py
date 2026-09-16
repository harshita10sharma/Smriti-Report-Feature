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

from analysis.models.enums import Direction, QualityStatus, TrendDirection


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
    contributing_observation_ids: tuple[str, ...] = ()

    @model_validator(mode="after")
    def _sample_count_is_positive(self) -> TrajectoryPoint:
        if self.sample_count < 1:
            raise ValueError(
                "a TrajectoryPoint must represent at least one observation; "
                "a period with zero observations must not appear at all"
            )
        return self

    @model_validator(mode="after")
    def _contributing_ids_match_sample_count_when_present(self) -> TrajectoryPoint:
        if self.contributing_observation_ids and (
            len(self.contributing_observation_ids) != self.sample_count
        ):
            raise ValueError(
                f"contributing_observation_ids has {len(self.contributing_observation_ids)} "
                f"entries but sample_count is {self.sample_count}"
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
    """The longitudinal trajectory of one metric for one patient.

    ``trend_direction`` is the neutral mathematical shape of the raw
    values over time; ``metric_direction`` is the registry's own
    favorability for this metric (e.g. LOWER_IS_BETTER for an error
    rate). The two are kept as separate fields deliberately - a
    consumer must consult both before ever describing a trend as
    "improving" or "declining", and this module performs no such
    interpretation itself.

    ``smoothing_method`` doubles as the general calculation-method
    label (e.g. "ordinary_least_squares_on_daily_median") - no actual
    smoothing (moving average, exponential weighting, etc.) is
    implemented as of this phase, only a slope fit over unsmoothed
    per-day points. ``slope``/``r_squared`` are ``None`` whenever
    ``trend_direction`` is ``None`` (insufficient points to fit one).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: str
    metric_id: str
    points: tuple[TrajectoryPoint, ...]
    smoothing_method: str | None
    trend_direction: TrendDirection | None
    metric_direction: Direction | None
    slope: float | None = None
    r_squared: float | None = None
    quality: QualityStatus
    excluded_observation_ids: tuple[str, ...] = ()
    exclusion_reasons: dict[str, str] = {}
    change_points: tuple[ChangePoint, ...] = ()

    @property
    def sample_count(self) -> int:
        return sum(point.sample_count for point in self.points)

    @model_validator(mode="after")
    def _exclusion_reasons_cover_excluded_ids(self) -> Trajectory:
        missing = set(self.excluded_observation_ids) - set(self.exclusion_reasons)
        if missing:
            raise ValueError(
                f"excluded_observation_ids without a matching exclusion "
                f"reason: {sorted(missing)}"
            )
        return self
