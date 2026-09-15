"""Deterministic domain-quality propagation (master spec S9).

Mirrors ``analysis.aggregation.quality.classify_quality`` in spirit
(a pure function, same ``QualityStatus`` enum, no new status concept)
but operates one level up: on how many of a domain's *registered
metrics* ended up usable/limited/insufficient/unavailable, rather than
on how many raw observations contributed to one metric.
"""

from __future__ import annotations

from analysis.models.enums import QualityStatus


def classify_domain_quality(
    *,
    total_registered: int,
    usable_count: int,
    limited_count: int,
    insufficient_count: int,
    unavailable_count: int,
) -> tuple[QualityStatus, str | None]:
    """Classify one domain's evidence quality from metric-level counts.

    ``usable_count`` is metrics with a non-``None`` value (quality
    ``SUFFICIENT`` or ``LIMITED``); ``limited_count`` is the subset of
    those that are specifically ``LIMITED``. The four counts must
    satisfy ``usable_count + insufficient_count + unavailable_count ==
    total_registered`` (enforced by ``DomainEvidence`` itself, not
    re-checked here).

    Deterministic rule, evaluated in order:

    1. No metrics registered for the domain at all -> ``UNAVAILABLE``.
       (Not reachable with the current registry - every domain has at
       least one registered metric - but this function does not
       assume that will always remain true.)
    2. No usable metrics, but at least one metric had some data that
       simply wasn't enough -> ``INSUFFICIENT``.
    3. No usable metrics, and every registered metric is gated/
       unavailable -> ``UNAVAILABLE``.
    4. At least one usable metric, and every registered metric for the
       domain is usable with no degradation (no LIMITED, INSUFFICIENT,
       or UNAVAILABLE metric at all) -> ``SUFFICIENT``.
    5. Otherwise (some usable evidence exists, but it is incomplete or
       partially degraded) -> ``LIMITED``. This is the common case
       while any metric for the domain remains telemetry-gated (master
       spec S9.7: a domain must never appear stronger merely because
       missing metrics were discarded).
    """
    if total_registered == 0:
        return QualityStatus.UNAVAILABLE, "no metrics are registered for this domain"

    if usable_count == 0:
        if insufficient_count > 0:
            return (
                QualityStatus.INSUFFICIENT,
                f"{insufficient_count} of {total_registered} registered metric(s) "
                "had some data but not enough to be usable; the rest were unavailable",
            )
        return (
            QualityStatus.UNAVAILABLE,
            f"none of the {total_registered} registered metric(s) for this domain "
            "are currently computable",
        )

    if limited_count == 0 and insufficient_count == 0 and unavailable_count == 0:
        return QualityStatus.SUFFICIENT, None

    return (
        QualityStatus.LIMITED,
        f"{usable_count} of {total_registered} registered metric(s) are usable "
        f"({limited_count} of those limited); {insufficient_count} insufficient, "
        f"{unavailable_count} unavailable",
    )
