"""The structured Evidence object (master spec S49).

Every report-worthy conclusion must be reproducible from one of
these: it is the layer between raw analytics/detection and the
caregiver/clinician narrative. ``confounder_context`` and
``engagement_status`` are kept as simple placeholders here rather
than as full dedicated models, because the confounder-assessment and
engagement-analysis engines (later phases) will define their own
richer output shapes; Evidence will be widened to reference those
directly once they exist, rather than guessing their shape now.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import Direction, Domain, EvidenceSeverity, QualityStatus
from analysis.models.trajectory import ChangePoint


class Evidence(BaseModel):
    """A single, traceable analytical finding.

    ``change_point`` is ``None`` for evidence that supports a
    "stable"/"insufficient data" conclusion rather than a detected
    change - Evidence is not exclusively for changes.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    evidence_id: str
    patient_id: str
    domain: Domain
    metric_ids: tuple[str, ...]
    game_ids: tuple[str, ...]
    baseline_period: tuple[date, date] | None
    comparison_period: tuple[date, date] | None
    change_point: ChangePoint | None
    direction: Direction | None
    severity: EvidenceSeverity
    persistent: bool | None
    concordant_metric_ids: tuple[str, ...]
    contradicting_metric_ids: tuple[str, ...]
    supporting_session_ids: tuple[str, ...]
    confounder_context: tuple[str, ...]
    engagement_status: QualityStatus
    confidence: float
    data_quality: QualityStatus
    rationale: str
    limitations: tuple[str, ...]

    @model_validator(mode="after")
    def _confidence_is_a_probability(self) -> Evidence:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {self.confidence}")
        return self

    @model_validator(mode="after")
    def _at_least_one_metric_and_session(self) -> Evidence:
        if not self.metric_ids:
            raise ValueError("evidence must reference at least one metric_id")
        if not self.supporting_session_ids:
            raise ValueError(
                "evidence must reference at least one supporting session_id "
                "so the finding is traceable back to real sessions"
            )
        return self
