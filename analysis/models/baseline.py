"""Personal baseline shape.

A baseline is the primary comparator for longitudinal change: PERSON
vs. THEIR OWN HISTORY, not a population norm (master spec S23/S38).
This module only defines the shape a baseline estimate takes; the
estimation logic itself (how center/variability are computed, what
minimum evidence is required) belongs to a later phase and must
inspect real observation density before choosing constants.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import BaselineStatus


class Baseline(BaseModel):
    """A personal baseline estimate for one metric.

    ``center``/``variability`` are ``None`` whenever ``status`` is not
    ``ESTABLISHED`` - an unestablished baseline must not expose
    numbers that look usable. ``excluded_observation_ids`` +
    ``exclusion_reasons`` together ensure that if a point was dropped
    from the estimate, the reason is recorded rather than the point
    silently vanishing (master spec S62).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: str
    metric_id: str
    status: BaselineStatus
    period_start: date | None
    period_end: date | None
    n_sessions: int
    n_days: int
    center: float | None
    variability: float | None
    excluded_observation_ids: tuple[str, ...] = ()
    exclusion_reasons: dict[str, str] = {}

    @model_validator(mode="after")
    def _established_requires_estimate(self) -> Baseline:
        if self.status == BaselineStatus.ESTABLISHED:
            if self.center is None or self.variability is None:
                raise ValueError(
                    "an ESTABLISHED baseline must have both center and "
                    "variability; got a None value for at least one"
                )
            if self.period_start is None or self.period_end is None:
                raise ValueError(
                    "an ESTABLISHED baseline must have a defined period"
                )
        else:
            if self.center is not None or self.variability is not None:
                raise ValueError(
                    f"a baseline with status={self.status.value!r} must not "
                    "expose center/variability values"
                )
        return self

    @model_validator(mode="after")
    def _exclusion_reasons_cover_excluded_ids(self) -> Baseline:
        missing = set(self.excluded_observation_ids) - set(self.exclusion_reasons)
        if missing:
            raise ValueError(
                f"excluded_observation_ids without a matching exclusion "
                f"reason: {sorted(missing)}"
            )
        return self
