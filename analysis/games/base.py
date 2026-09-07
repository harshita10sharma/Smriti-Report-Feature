"""Shared building blocks for game-specific analyzers (master spec S76).

Every analyzer module exposes one function, ``analyze(patient_id,
session_id, ts, trials) -> GameAnalysisResult``, and uses only the
helpers below to build its ``MetricObservation`` values - this keeps
the "never fabricate, never promote an unverified field" rule
enforced in one place rather than repeated per game.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from statistics import median, pstdev

from pydantic import BaseModel, ConfigDict

from analysis.models.enums import GameId, QualityStatus, TelemetrySource
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


class GameAnalysisResult(BaseModel):
    """Every metric observation produced for one game session."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    patient_id: str
    session_id: str
    game_id: GameId
    trial_count: int
    observations: tuple[MetricObservation, ...]


def gated_unavailable(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int
) -> MetricObservation:
    """Build the UNAVAILABLE observation for a metric whose telemetry
    source is not actually verified.

    Callers must invoke this - and never attempt to compute a value -
    for any metric whose ``telemetry_source`` is
    ``METRICS_JSONB_UNVERIFIED`` or ``CROSS_TABLE_UNVERIFIED``.
    """
    return MetricObservation(
        metric_id=metric.metric_id,
        patient_id=patient_id,
        session_id=session_id,
        event_id=None,
        game_id=metric.game_id.value,
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        unavailable_reason=(
            f"telemetry_source={metric.telemetry_source.value}: {metric.verification_note}"
        ),
        ts=ts,
    )


def insufficient_observations(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    n_valid: int,
) -> MetricObservation:
    """Build the UNAVAILABLE observation when there are too few valid
    trials to meet ``metric.minimum_observations``."""
    return MetricObservation(
        metric_id=metric.metric_id,
        patient_id=patient_id,
        session_id=session_id,
        event_id=None,
        game_id=metric.game_id.value,
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        unavailable_reason=(
            f"only {n_valid} valid observation(s) available, "
            f"minimum_observations={metric.minimum_observations}"
        ),
        ts=ts,
    )


def observation(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    value: float,
    quality: QualityStatus = QualityStatus.SUFFICIENT,
) -> MetricObservation:
    """Build a usable observation with an actual computed value."""
    return MetricObservation(
        metric_id=metric.metric_id,
        patient_id=patient_id,
        session_id=session_id,
        event_id=None,
        game_id=metric.game_id.value,
        value=value,
        quality=quality,
        unavailable_reason=None,
        ts=ts,
    )


def require_verified(metric: RegisteredMetric) -> None:
    """Defensive guard: raise if this function is ever called for a
    metric that is not backed by verified telemetry.

    Every ``_compute_*`` helper below calls this first, so a future
    registry edit that changes a metric's ``telemetry_source`` to an
    unverified value cannot silently start being "computed" from a
    Trial's ``metrics`` payload - it would raise instead.
    """
    if metric.telemetry_source not in (
        TelemetrySource.VERIFIED_COLUMN,
        TelemetrySource.DERIVED_FROM_VERIFIED_COLUMNS,
    ):
        raise AssertionError(
            f"{metric.metric_id}: attempted to compute a value for a "
            f"metric whose telemetry_source is "
            f"{metric.telemetry_source.value!r}; only gated_unavailable() "
            "may be used for this metric until its telemetry is confirmed"
        )


def compute_rate(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
    is_eligible: Callable[[Trial], bool],
    is_positive: Callable[[Trial], bool],
) -> MetricObservation:
    """Compute a proportion metric: positive count / eligible count.

    ``is_eligible`` selects which trials count toward the denominator
    (e.g. "has a non-null correct value"); ``is_positive`` selects the
    numerator among eligible trials.
    """
    require_verified(metric)
    eligible = [t for t in trials if is_eligible(t)]
    if len(eligible) < metric.minimum_observations:
        return insufficient_observations(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, n_valid=len(eligible)
        )
    positive_count = sum(1 for t in eligible if is_positive(t))
    return observation(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        value=positive_count / len(eligible),
    )


def compute_dispersion(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
    extractor: Callable[[Trial], float | None],
    use_median: bool = False,
) -> MetricObservation:
    """Compute a standard deviation (default) or median over a numeric
    field extracted from each trial, skipping trials where the field
    is absent."""
    require_verified(metric)
    values = [v for t in trials if (v := extractor(t)) is not None]
    if len(values) < metric.minimum_observations:
        return insufficient_observations(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, n_valid=len(values)
        )
    result = median(values) if use_median else pstdev(values)
    return observation(
        metric, patient_id=patient_id, session_id=session_id, ts=ts, value=result
    )


def compute_count(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
    is_eligible: Callable[[Trial], bool],
) -> MetricObservation:
    """Compute a simple count of eligible trials."""
    require_verified(metric)
    count = sum(1 for t in trials if is_eligible(t))
    if len(trials) < metric.minimum_observations:
        return insufficient_observations(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, n_valid=len(trials)
        )
    return observation(
        metric, patient_id=patient_id, session_id=session_id, ts=ts, value=float(count)
    )
