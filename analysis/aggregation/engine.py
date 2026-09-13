"""Registry-driven aggregation (master spec S12-S19, S21).

Seven public functions, one per ``AggregationMethod`` value:
``aggregate_mean``, ``aggregate_median``, ``aggregate_max_achieved``,
``aggregate_rate``, ``aggregate_stddev``, ``aggregate_count`` (all take
one flat list of ``RawObservation``), and ``aggregate_difference``
(takes two groups - it compares them, so a flat list makes no sense).

Every function:

1. Refuses to run at all unless ``metric.telemetry_source`` is
   verified (``require_verified``) - mirroring the same gate
   ``analysis.games.base`` enforces for Phase 4, so a metric can never
   be "computed" here just because Phase 4 declined to.
2. Excludes (never clips or fabricates) any present value outside
   ``metric.valid_range``, recording why.
3. Classifies the result's quality via ``analysis.aggregation.quality
   .classify_quality`` - the same deterministic rule for every method.
4. Returns an ``AggregationResult`` that preserves every contributing
   source id, the missing/excluded counts, and the excluded records
   themselves.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from typing import Literal

from analysis.aggregation.models import AggregationResult, ExcludedObservation, RawObservation
from analysis.aggregation.quality import classify_quality
from analysis.models.enums import QualityStatus
from analysis.registry.metrics import VERIFIED_TELEMETRY_SOURCES, RegisteredMetric


def require_verified(metric: RegisteredMetric) -> None:
    """Raise if ``metric`` is not backed by verified telemetry.

    Mirrors ``analysis.games.base.require_verified`` exactly (see
    ``RegisteredMetric.VERIFIED_TELEMETRY_SOURCES`` for why the two
    are not literally the same function): this package must not
    silently start "computing" a metric Phase 4 correctly refuses to.
    """
    if metric.telemetry_source not in VERIFIED_TELEMETRY_SOURCES:
        raise AssertionError(
            f"{metric.metric_id}: attempted to aggregate a metric whose "
            f"telemetry_source is {metric.telemetry_source.value!r}; only "
            "metrics with verified telemetry may be aggregated"
        )


class _Partitioned:
    """Internal result of splitting raw observations into usable
    values, missing count, and excluded (invalid-range) records."""

    __slots__ = ("eligible_values", "eligible_ids", "missing_count", "excluded", "ts_values")

    def __init__(
        self,
        eligible_values: list[float],
        eligible_ids: list[str],
        missing_count: int,
        excluded: tuple[ExcludedObservation, ...],
        ts_values: list[int],
    ) -> None:
        self.eligible_values = eligible_values
        self.eligible_ids = eligible_ids
        self.missing_count = missing_count
        self.excluded = excluded
        self.ts_values = ts_values


def _partition(
    metric: RegisteredMetric, observations: Sequence[RawObservation]
) -> _Partitioned:
    """Split raw observations into eligible values / missing / excluded.

    Only applies ``metric.valid_range`` to each individual raw value -
    appropriate for MEAN/MEDIAN/MAX_ACHIEVED/RATE/STDDEV/COUNT, where
    the range describes every contributing value. It is deliberately
    NOT used this way for DIFFERENCE metrics (see
    ``aggregate_difference``), whose ``valid_range`` describes the
    *computed difference*, not each raw pre/post value.
    """
    eligible_values: list[float] = []
    eligible_ids: list[str] = []
    ts_values: list[int] = []
    excluded: list[ExcludedObservation] = []
    missing_count = 0

    for obs in observations:
        if obs.value is None:
            missing_count += 1
            continue
        if metric.valid_range is not None:
            low, high = metric.valid_range
            if not (low <= obs.value <= high):
                excluded.append(
                    ExcludedObservation(
                        source_id=obs.source_id,
                        reason_code="outside_valid_range",
                        reason_message=(
                            f"value {obs.value} is outside the metric's valid "
                            f"range [{low}, {high}]"
                        ),
                    )
                )
                continue
        eligible_values.append(obs.value)
        eligible_ids.append(obs.source_id)
        ts_values.append(obs.ts)

    return _Partitioned(eligible_values, eligible_ids, missing_count, tuple(excluded), ts_values)


def _ts_range(ts_values: Sequence[int]) -> tuple[int, int] | None:
    return (min(ts_values), max(ts_values)) if ts_values else None


def _finalize(
    metric: RegisteredMetric,
    patient_id: str,
    partitioned: _Partitioned,
    value: float | None,
) -> AggregationResult:
    """Classify quality, apply the output-range safety check, and
    build the final AggregationResult.

    ``value`` must already be computed from ``partitioned.eligible_values``
    (or be ``None`` if the caller could not compute one); this function
    forces it back to ``None`` whenever quality resolves to
    UNAVAILABLE/INSUFFICIENT, regardless of what was passed in, so a
    caller bug can never leak a number past a failed quality check.
    """
    quality, reason = classify_quality(
        valid_count=len(partitioned.eligible_values),
        excluded_count=len(partitioned.excluded),
        missing_count=partitioned.missing_count,
        minimum_observations=metric.minimum_observations,
    )

    if quality in (QualityStatus.UNAVAILABLE, QualityStatus.INSUFFICIENT):
        value = None
    elif value is not None and metric.valid_range is not None:
        low, high = metric.valid_range
        if not (low <= value <= high):
            quality = QualityStatus.LIMITED
            reason = (
                f"computed value {value} falls outside the metric's expected "
                f"valid_range [{low}, {high}]; result retained but should be "
                "treated with caution"
            )

    return AggregationResult(
        metric_id=metric.metric_id,
        patient_id=patient_id,
        game_id=metric.game_id,
        aggregation=metric.aggregation,
        value=value,
        quality=quality,
        reason=reason,
        valid_count=len(partitioned.eligible_values),
        missing_count=partitioned.missing_count,
        excluded=partitioned.excluded,
        source_ids=tuple(partitioned.eligible_ids),
        ts_range=_ts_range(partitioned.ts_values),
    )


def aggregate_mean(
    metric: RegisteredMetric, patient_id: str, observations: Sequence[RawObservation]
) -> AggregationResult:
    """Arithmetic mean of eligible values."""
    require_verified(metric)
    partitioned = _partition(metric, observations)
    value = statistics.mean(partitioned.eligible_values) if partitioned.eligible_values else None
    return _finalize(metric, patient_id, partitioned, value)


def aggregate_median(
    metric: RegisteredMetric, patient_id: str, observations: Sequence[RawObservation]
) -> AggregationResult:
    """Median of eligible values - robust to skew, used for timing
    metrics per the registry's own aggregation choice."""
    require_verified(metric)
    partitioned = _partition(metric, observations)
    value = (
        statistics.median(partitioned.eligible_values) if partitioned.eligible_values else None
    )
    return _finalize(metric, patient_id, partitioned, value)


def aggregate_stddev(
    metric: RegisteredMetric, patient_id: str, observations: Sequence[RawObservation]
) -> AggregationResult:
    """Population standard deviation of eligible values.

    ``classify_quality`` already enforces ``minimum_observations``;
    metrics using STDDEV should set it to at least 2, since a
    dispersion estimate from a single point is not meaningful even
    though ``statistics.pstdev`` would happily return 0.0 for it.
    """
    require_verified(metric)
    partitioned = _partition(metric, observations)
    value = (
        statistics.pstdev(partitioned.eligible_values) if partitioned.eligible_values else None
    )
    return _finalize(metric, patient_id, partitioned, value)


def aggregate_count(
    metric: RegisteredMetric, patient_id: str, observations: Sequence[RawObservation]
) -> AggregationResult:
    """Count of eligible observations.

    Counts the *observations*, not their values - each eligible
    ``RawObservation`` represents exactly one countable entity (master
    spec S19: count only the entity the metric actually defines; the
    caller is responsible for only supplying one RawObservation per
    entity it can actually confirm exists).
    """
    require_verified(metric)
    partitioned = _partition(metric, observations)
    value = float(len(partitioned.eligible_values)) if partitioned.eligible_values else None
    return _finalize(metric, patient_id, partitioned, value)


def aggregate_max_achieved(
    metric: RegisteredMetric, patient_id: str, observations: Sequence[RawObservation]
) -> AggregationResult:
    """Maximum eligible value - for span-type metrics representing
    the highest level actually achieved, not an average performance."""
    require_verified(metric)
    partitioned = _partition(metric, observations)
    value = max(partitioned.eligible_values) if partitioned.eligible_values else None
    return _finalize(metric, patient_id, partitioned, value)


def aggregate_rate(
    metric: RegisteredMetric, patient_id: str, observations: Sequence[RawObservation]
) -> AggregationResult:
    """Proportion of eligible observations that are positive.

    Each ``RawObservation.value`` must be exactly ``0.0`` (negative/
    ineligible) or ``1.0`` (positive) - representing one already-
    eligible trial/entity the caller has confirmed belongs in the
    denominator (master spec S16: the denominator must be supported
    by actual telemetry, never manufactured; do not pass observations
    for entities that were never eligible in the first place). A
    value that is present but not exactly 0.0/1.0 is excluded, not
    rounded or coerced.
    """
    require_verified(metric)
    partitioned = _partition(metric, observations)

    valid_indicator_values: list[float] = []
    valid_indicator_ids: list[str] = []
    valid_indicator_ts: list[int] = []
    extra_excluded: list[ExcludedObservation] = []
    for value, source_id, ts in zip(
        partitioned.eligible_values, partitioned.eligible_ids, partitioned.ts_values, strict=True
    ):
        if value not in (0.0, 1.0):
            extra_excluded.append(
                ExcludedObservation(
                    source_id=source_id,
                    reason_code="invalid_rate_indicator",
                    reason_message=(
                        f"value {value} is not a valid rate indicator "
                        "(expected exactly 0.0 or 1.0)"
                    ),
                )
            )
            continue
        valid_indicator_values.append(value)
        valid_indicator_ids.append(source_id)
        valid_indicator_ts.append(ts)

    refined = _Partitioned(
        eligible_values=valid_indicator_values,
        eligible_ids=valid_indicator_ids,
        missing_count=partitioned.missing_count,
        excluded=partitioned.excluded + tuple(extra_excluded),
        ts_values=valid_indicator_ts,
    )
    rate = (
        sum(valid_indicator_values) / len(valid_indicator_values)
        if valid_indicator_values
        else None
    )
    return _finalize(metric, patient_id, refined, rate)


def aggregate_difference(
    metric: RegisteredMetric,
    patient_id: str,
    before: Sequence[RawObservation],
    after: Sequence[RawObservation],
    *,
    combine: Literal["mean", "median"] = "mean",
) -> AggregationResult:
    """Compare a "before" group against an "after" group: value =
    summary(after) - summary(before) (post-switch minus pre-switch, B
    minus A, last block minus first block - the registry's DIFFERENCE
    metrics are all phrased this way).

    Unlike the single-list aggregations, ``metric.valid_range`` is
    NOT applied to individual before/after values here - for a
    DIFFERENCE metric that range describes the *computed difference*
    (e.g. a decline-of-two-proportions bounded to [-1, 1]), not each
    raw contributing value, which may have an entirely different
    natural range. Master spec S17: never infer missing comparison
    groups from event order alone - the caller must have already
    partitioned observations into genuine before/after groups (e.g.
    via a confirmed rule-boundary or block marker), not by position.
    """
    require_verified(metric)
    summarize = statistics.mean if combine == "mean" else statistics.median

    before_partitioned = _partition(metric.model_copy(update={"valid_range": None}), before)
    after_partitioned = _partition(metric.model_copy(update={"valid_range": None}), after)

    combined_missing = before_partitioned.missing_count + after_partitioned.missing_count
    combined_excluded = before_partitioned.excluded + after_partitioned.excluded
    combined_ids = tuple(before_partitioned.eligible_ids) + tuple(after_partitioned.eligible_ids)
    combined_ts = before_partitioned.ts_values + after_partitioned.ts_values

    value: float | None = None
    if before_partitioned.eligible_values and after_partitioned.eligible_values:
        value = summarize(after_partitioned.eligible_values) - summarize(
            before_partitioned.eligible_values
        )

    combined = _Partitioned(
        eligible_values=before_partitioned.eligible_values + after_partitioned.eligible_values,
        eligible_ids=list(combined_ids),
        missing_count=combined_missing,
        excluded=combined_excluded,
        ts_values=combined_ts,
    )
    # A DIFFERENCE needs both groups non-empty to mean anything; if
    # either is empty, valid_count must reflect "not enough to compare"
    # even though individual values might otherwise look sufficient.
    if not before_partitioned.eligible_values or not after_partitioned.eligible_values:
        combined.eligible_values = []
        combined.eligible_ids = []
    return _finalize(metric, patient_id, combined, value)
