"""Registry-driven domain estimation (master spec S4-S13).

``estimate_domain`` is the one function that turns Phase 5's
``AggregationResult`` objects into structured evidence for a single
cognitive domain. It never computes a composite score: every
registered metric (``analysis.registry.metrics_for_domain``) becomes
its own ``MetricEvidenceEntry``, preserving its own value, direction,
and quality, and the domain-level ``quality`` field
(``analysis.domains.quality.classify_domain_quality``) describes
evidence coverage only.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.aggregation.models import AggregationResult
from analysis.domains.models import DomainEvidence, MetricEvidenceEntry
from analysis.domains.quality import classify_domain_quality
from analysis.errors import PatientIsolationError, RegistryError
from analysis.models.enums import Domain, GameId, QualityStatus
from analysis.registry import metrics_for_domain
from analysis.registry.metrics import VERIFIED_TELEMETRY_SOURCES, RegisteredMetric


def _gated_entry(metric: RegisteredMetric) -> MetricEvidenceEntry:
    return MetricEvidenceEntry(
        metric_id=metric.metric_id,
        game_id=metric.game_id,
        direction=metric.direction,
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        reason=(
            f"telemetry_source={metric.telemetry_source.value}: {metric.verification_note}"
        ),
        source_ids=(),
        valid_count=0,
    )


def _missing_result_entry(metric: RegisteredMetric) -> MetricEvidenceEntry:
    return MetricEvidenceEntry(
        metric_id=metric.metric_id,
        game_id=metric.game_id,
        direction=metric.direction,
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        reason="no aggregation result was supplied for this metric",
        source_ids=(),
        valid_count=0,
    )


def _entry_from_result(metric: RegisteredMetric, result: AggregationResult) -> MetricEvidenceEntry:
    return MetricEvidenceEntry(
        metric_id=metric.metric_id,
        game_id=result.game_id,
        direction=metric.direction,
        value=result.value,
        quality=result.quality,
        reason=result.reason,
        source_ids=result.source_ids,
        valid_count=result.valid_count,
    )


def estimate_domain(
    domain: Domain, patient_id: str, results: Sequence[AggregationResult]
) -> DomainEvidence:
    """Build structured evidence for one cognitive domain.

    ``results`` should contain the Phase 5 ``AggregationResult`` for
    every *verified* metric registered to this domain that the caller
    actually computed; results for metrics outside this domain are
    ignored. A registered metric with no verified telemetry source is
    never expected to have a result at all - it is classified as
    ``UNAVAILABLE`` directly from the registry, without requiring the
    caller to fabricate a placeholder. A verified metric with no
    corresponding result is also ``UNAVAILABLE`` (distinctly reasoned)
    rather than silently skipped, so domain evidence never omits a
    registered metric.

    Raises ``PatientIsolationError`` if a supplied result's
    ``patient_id`` does not match ``patient_id`` - this must never
    happen if callers scope their aggregation calls correctly, but is
    checked defensively rather than assumed (master spec S15).
    """
    registered = metrics_for_domain(domain)
    results_by_id = {result.metric_id: result for result in results}

    entries: list[MetricEvidenceEntry] = []
    usable_ids: list[str] = []
    limited_ids: list[str] = []
    insufficient_ids: list[str] = []
    unavailable_ids: list[str] = []
    usable_observation_count = 0
    contributing_games: set[GameId] = set()

    for metric in registered:
        if metric.telemetry_source not in VERIFIED_TELEMETRY_SOURCES:
            entries.append(_gated_entry(metric))
            unavailable_ids.append(metric.metric_id)
            continue

        result = results_by_id.get(metric.metric_id)
        if result is None:
            entries.append(_missing_result_entry(metric))
            unavailable_ids.append(metric.metric_id)
            continue

        if result.patient_id != patient_id:
            raise PatientIsolationError(
                f"{metric.metric_id}: aggregation result belongs to patient "
                f"{result.patient_id!r}, but domain estimation was requested "
                f"for patient {patient_id!r}"
            )
        if result.game_id != metric.game_id:
            raise RegistryError(
                f"{metric.metric_id}: aggregation result's game_id "
                f"{result.game_id.value!r} does not match the registry's "
                f"{metric.game_id.value!r}"
            )

        entries.append(_entry_from_result(metric, result))

        if result.quality in (QualityStatus.SUFFICIENT, QualityStatus.LIMITED):
            usable_ids.append(metric.metric_id)
            usable_observation_count += result.valid_count
            contributing_games.add(metric.game_id)
            if result.quality == QualityStatus.LIMITED:
                limited_ids.append(metric.metric_id)
        elif result.quality == QualityStatus.INSUFFICIENT:
            insufficient_ids.append(metric.metric_id)
        else:
            unavailable_ids.append(metric.metric_id)

    quality, reason = classify_domain_quality(
        total_registered=len(registered),
        usable_count=len(usable_ids),
        limited_count=len(limited_ids),
        insufficient_count=len(insufficient_ids),
        unavailable_count=len(unavailable_ids),
    )

    return DomainEvidence(
        patient_id=patient_id,
        domain=domain,
        quality=quality,
        reason=reason,
        metric_evidence=tuple(entries),
        contributing_game_ids=tuple(sorted(contributing_games, key=lambda g: g.value)),
        usable_metric_ids=tuple(usable_ids),
        limited_metric_ids=tuple(limited_ids),
        insufficient_metric_ids=tuple(insufficient_ids),
        unavailable_metric_ids=tuple(unavailable_ids),
        usable_observation_count=usable_observation_count,
    )


def estimate_all_domains(
    patient_id: str, results: Sequence[AggregationResult]
) -> dict[Domain, DomainEvidence]:
    """Convenience wrapper: estimate all five domains from one shared
    pool of aggregation results.

    Each domain independently filters ``results`` down to its own
    registered metrics via ``estimate_domain`` - passing the full pool
    to every domain is safe and does not cause cross-domain
    contamination.
    """
    return {domain: estimate_domain(domain, patient_id, results) for domain in Domain}
