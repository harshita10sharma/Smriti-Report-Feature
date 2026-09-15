"""Typed domain-estimation output (master spec S6, S10).

No field here is a composite domain score - ``DomainEvidence``
preserves every registered metric's own value, direction, and quality
individually (``MetricEvidenceEntry``), plus coverage counts. Metrics
with incompatible units/scales must never be averaged into one number
(master spec S11/S12); this model structurally makes that impossible
since there is nowhere to put such a number.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import Direction, Domain, GameId, QualityStatus


class MetricEvidenceEntry(BaseModel):
    """One registered metric's contribution to a domain's evidence.

    Present for *every* metric ``analysis.registry.metrics_for_domain``
    returns for the domain - including gated/unavailable ones - so a
    domain's evidence never silently omits a metric that could not be
    computed (master spec S9.7: a domain must never appear stronger
    merely because missing metrics were discarded).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    metric_id: str
    game_id: GameId
    direction: Direction
    value: float | None
    quality: QualityStatus
    reason: str | None
    source_ids: tuple[str, ...]
    valid_count: int

    @model_validator(mode="after")
    def _value_requires_no_reason_and_vice_versa(self) -> MetricEvidenceEntry:
        if self.value is None and self.reason is None:
            raise ValueError(
                f"{self.metric_id}: reason is required whenever value is None"
            )
        return self


class DomainEvidence(BaseModel):
    """Structured evidence for one cognitive domain, for one patient.

    ``quality`` describes evidence *coverage/reliability*, never
    cognitive performance - it must not be read as "how well the
    person is doing" (that judgment belongs to a later phase's
    report-state logic, built on top of trajectories this phase does
    not compute).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: str
    domain: Domain
    quality: QualityStatus
    reason: str | None
    metric_evidence: tuple[MetricEvidenceEntry, ...]
    contributing_game_ids: tuple[GameId, ...]
    usable_metric_ids: tuple[str, ...]
    limited_metric_ids: tuple[str, ...]
    insufficient_metric_ids: tuple[str, ...]
    unavailable_metric_ids: tuple[str, ...]
    usable_observation_count: int

    @property
    def total_registered_domain_metrics(self) -> int:
        return len(self.metric_evidence)

    @model_validator(mode="after")
    def _value_requires_no_reason_and_vice_versa(self) -> DomainEvidence:
        if self.quality in (QualityStatus.UNAVAILABLE, QualityStatus.INSUFFICIENT):
            if self.reason is None:
                raise ValueError(
                    f"{self.domain.value}: reason is required when domain quality "
                    f"is {self.quality.value}"
                )
        return self

    @model_validator(mode="after")
    def _metric_id_buckets_partition_all_evidence(self) -> DomainEvidence:
        all_ids = {entry.metric_id for entry in self.metric_evidence}
        bucketed = (
            set(self.usable_metric_ids)
            | set(self.insufficient_metric_ids)
            | set(self.unavailable_metric_ids)
        )
        if bucketed != all_ids:
            raise ValueError(
                f"{self.domain.value}: usable+insufficient+unavailable metric_ids "
                f"{sorted(bucketed)} do not match metric_evidence's metric_ids "
                f"{sorted(all_ids)}"
            )
        if not set(self.limited_metric_ids) <= set(self.usable_metric_ids):
            raise ValueError(
                f"{self.domain.value}: limited_metric_ids must be a subset of "
                "usable_metric_ids"
            )
        return self

    @model_validator(mode="after")
    def _usable_observation_count_is_non_negative(self) -> DomainEvidence:
        if self.usable_observation_count < 0:
            raise ValueError(
                f"{self.domain.value}: usable_observation_count must not be negative"
            )
        return self
