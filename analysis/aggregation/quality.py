"""Deterministic quality-state propagation (master spec S8, S9, S27).

``classify_quality`` is a pure function: given only counts (never the
actual values), it decides the ``QualityStatus`` and a human-readable
reason for one aggregation. Keeping it pure and separate from the
aggregation math itself makes the propagation rule independently
testable and guarantees every aggregation method applies exactly the
same rule.
"""

from __future__ import annotations

from analysis.models.enums import QualityStatus

#: If more than this fraction of candidate observations were excluded
#: (invalid) or missing - even though enough valid ones remain to meet
#: minimum_observations - the result is downgraded from SUFFICIENT to
#: LIMITED. Purpose: prevent a single valid observation from disguising
#: a mostly-missing/invalid data window as fully trustworthy (master
#: spec S27: "do not let a single valid observation hide a large
#: amount of missing or invalid data"). Units: none (a ratio in [0, 1]).
#: Rationale for 0.5: the point at which excluded+missing observations
#: outnumber retained ones. This is an engineering judgment call, not
#: a value derived from clinical data, and should be revisited once
#: real telemetry volume is available (master spec S49).
EXCESSIVE_EXCLUSION_RATIO = 0.5


def classify_quality(
    *,
    valid_count: int,
    excluded_count: int,
    missing_count: int,
    minimum_observations: int,
) -> tuple[QualityStatus, str | None]:
    """Classify one aggregation's quality from its contributing counts.

    Deterministic rule, evaluated in order:

    1. No candidate observations at all -> ``UNAVAILABLE``.
    2. Valid count below ``minimum_observations`` -> ``INSUFFICIENT``.
    3. Excluded+missing exceed ``EXCESSIVE_EXCLUSION_RATIO`` of all
       candidates -> ``LIMITED``.
    4. Otherwise -> ``SUFFICIENT``.

    The reason string is ``None`` only in the ``SUFFICIENT`` case with
    zero exclusions - every degraded state always explains itself.
    """
    total_candidates = valid_count + excluded_count + missing_count
    if total_candidates == 0:
        return QualityStatus.UNAVAILABLE, "no observations were supplied"

    if valid_count < minimum_observations:
        return (
            QualityStatus.INSUFFICIENT,
            f"only {valid_count} valid observation(s) available "
            f"(minimum_observations={minimum_observations}); "
            f"{excluded_count} excluded, {missing_count} missing",
        )

    non_valid_count = excluded_count + missing_count
    if non_valid_count > 0 and non_valid_count / total_candidates > EXCESSIVE_EXCLUSION_RATIO:
        return (
            QualityStatus.LIMITED,
            f"{non_valid_count} of {total_candidates} candidate observations "
            f"were excluded or missing ({excluded_count} excluded, "
            f"{missing_count} missing), exceeding the "
            f"{EXCESSIVE_EXCLUSION_RATIO:.0%} threshold",
        )

    return QualityStatus.SUFFICIENT, None
