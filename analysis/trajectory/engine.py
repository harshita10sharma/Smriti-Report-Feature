"""Longitudinal trajectory estimation.

``estimate_trajectory`` turns a patient's session-by-session
``BaselineObservation`` history for one metric into a
``analysis.models.trajectory.Trajectory``: a neutral, purely
mathematical description of how the metric's raw value has moved over
time (increasing/decreasing/stable), never a judgment about whether
that movement is clinically favorable.

Unlike ``analysis.baseline.engine.estimate_baseline``, there is no
lookback window here - a trajectory is meant to show the metric's
whole verified history up to ``as_of``, not a fixed recent slice. The
only temporal restriction is the cutoff itself (master spec S29: never
let a historical calculation see future data).
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import date
from typing import NamedTuple

from analysis.baseline.models import BaselineObservation
from analysis.baseline.temporal import filter_by_cutoff_date
from analysis.errors import PatientIsolationError, RegistryError
from analysis.models.enums import Direction, Domain, QualityStatus, TrendDirection
from analysis.models.trajectory import Trajectory, TrajectoryPoint
from analysis.registry import metrics_for_domain
from analysis.registry.metric_registry import METRIC_REGISTRY
from analysis.registry.metrics import VERIFIED_TELEMETRY_SOURCES
from analysis.trajectory.config import MINIMUM_TRAJECTORY_POINTS, STABLE_THRESHOLD_RATIO

#: The only calculation method implemented so far - an ordinary least
#: squares line fit through one median-of-day point per distinct
#: calendar day with usable evidence. No smoothing (moving average,
#: exponential weighting, etc.) is applied.
_CALCULATION_METHOD = "ordinary_least_squares_on_daily_median"


class _FitResult(NamedTuple):
    slope: float
    r_squared: float


def _validated_observations(
    patient_id: str,
    metric_id: str,
    observations: Sequence[BaselineObservation],
    as_of: date,
) -> list[BaselineObservation]:
    """Check patient/metric identity, then return every observation
    with ``observed_on <= as_of``, ordered by date and (for
    determinism when two sessions share a date) by session_id.

    Raises ``PatientIsolationError``/``RegistryError`` for a caller
    contract violation - defensive checks that should never trigger if
    callers scope their queries correctly.
    """
    for obs in observations:
        if obs.result.patient_id != patient_id:
            raise PatientIsolationError(
                f"{metric_id}: observation for session {obs.session_id!r} belongs "
                f"to patient {obs.result.patient_id!r}, but trajectory estimation "
                f"was requested for patient {patient_id!r}"
            )
        if obs.result.metric_id != metric_id:
            raise RegistryError(
                f"observation for session {obs.session_id!r} is for metric "
                f"{obs.result.metric_id!r}, but trajectory estimation was "
                f"requested for metric {metric_id!r}"
            )

    cutoff_applied = filter_by_cutoff_date(observations, cutoff=as_of)
    return sorted(cutoff_applied, key=lambda o: (o.observed_on, o.session_id))


def _fit_line(x_values: Sequence[float], y_values: Sequence[float]) -> _FitResult:
    """Ordinary least squares slope and R-squared for two equal-length
    sequences.

    Callers only invoke this once at least ``MINIMUM_TRAJECTORY_POINTS``
    distinct-day points exist, and points are keyed by distinct
    calendar day, so ``x_values`` always has more than one distinct
    value here - the classic "zero x-variance" division-by-zero case
    cannot arise. The one edge case handled explicitly is zero
    y-variance (every point has the identical raw value): the fitted
    line is flat (slope 0.0) and, since there is no variance to
    explain, R-squared is defined as a perfect 1.0 rather than the
    undefined 0/0 that the standard formula would otherwise produce.
    """
    mean_x = statistics.fmean(x_values)
    mean_y = statistics.fmean(y_values)
    ss_xx = sum((x - mean_x) ** 2 for x in x_values)
    ss_yy = sum((y - mean_y) ** 2 for y in y_values)

    if ss_yy == 0.0:
        return _FitResult(slope=0.0, r_squared=1.0)

    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values, strict=True))
    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x
    ss_res = sum(
        (y - (slope * x + intercept)) ** 2 for x, y in zip(x_values, y_values, strict=True)
    )
    r_squared = 1.0 - (ss_res / ss_yy)
    return _FitResult(slope=slope, r_squared=r_squared)


def _classify_trend(slope: float, span_days: float, raw_values: Sequence[float]) -> TrendDirection:
    """Classify a fitted slope as INCREASING/DECREASING/STABLE.

    A slope is STABLE unless the total change it predicts across the
    observed time span exceeds ``STABLE_THRESHOLD_RATIO`` of the
    trajectory's own robust variability (median absolute deviation of
    its raw values) - see ``analysis.trajectory.config`` for why a
    relative, per-metric threshold is used instead of an arbitrary
    absolute number.
    """
    center = statistics.median(raw_values)
    mad = statistics.median(abs(value - center) for value in raw_values)
    if mad == 0.0:
        # No variability at all in the raw values - by definition not
        # a meaningful increase or decrease, regardless of slope sign.
        return TrendDirection.STABLE

    predicted_total_change = abs(slope) * span_days
    if predicted_total_change < STABLE_THRESHOLD_RATIO * mad:
        return TrendDirection.STABLE
    return TrendDirection.INCREASING if slope > 0 else TrendDirection.DECREASING


def _registered_direction(metric_id: str) -> Direction | None:
    """Look up a metric's favorability from the registry, never
    hard-coded or assumed - ``None`` when the metric is not (yet)
    registered."""
    metric = METRIC_REGISTRY.get(metric_id)
    return metric.direction if metric is not None else None


def estimate_trajectory(
    patient_id: str,
    metric_id: str,
    observations: Sequence[BaselineObservation],
    as_of: date,
) -> Trajectory:
    """Estimate the longitudinal trajectory of one patient/metric as of
    a date.

    Every observation with ``observed_on <= as_of`` is considered;
    nothing after that date is inspected at all (master spec S29). An
    observation that is not ``is_usable`` (quality INSUFFICIENT or
    UNAVAILABLE) is recorded in ``excluded_observation_ids``/
    ``exclusion_reasons`` rather than silently dropped or treated as
    zero. Usable observations sharing a calendar day are collapsed
    into one ``TrajectoryPoint`` using their median value - a period
    with no usable evidence at all is simply absent, never a
    manufactured zero-sample point.

    A trend is only computed once at least ``MINIMUM_TRAJECTORY_POINTS``
    distinct days of usable evidence exist; below that, the trajectory
    is returned with ``trend_direction``/``slope``/``r_squared`` all
    ``None`` and quality ``INSUFFICIENT`` (or ``UNAVAILABLE`` if there
    is no usable evidence at all).
    """
    ordered = _validated_observations(patient_id, metric_id, observations, as_of)

    usable = [obs for obs in ordered if obs.is_usable]
    excluded = [obs for obs in ordered if not obs.is_usable]
    excluded_ids = tuple(obs.session_id for obs in excluded)
    exclusion_reasons = {
        obs.session_id: (obs.result.reason or "no reason recorded") for obs in excluded
    }
    metric_direction = _registered_direction(metric_id)

    days: dict[date, list[BaselineObservation]] = {}
    for obs in usable:
        days.setdefault(obs.observed_on, []).append(obs)

    points = tuple(
        TrajectoryPoint(
            period_start=day,
            period_end=day,
            raw_value=statistics.median(
                obs.result.value for obs in day_obs if obs.result.value is not None
            ),
            normalized_value=None,
            smoothed_value=None,
            sample_count=len(day_obs),
            quality=QualityStatus.SUFFICIENT,
            contributing_observation_ids=tuple(
                sorted(obs.session_id for obs in day_obs)
            ),
        )
        for day, day_obs in sorted(days.items())
    )

    if len(points) == 0:
        return Trajectory(
            patient_id=patient_id,
            metric_id=metric_id,
            points=(),
            smoothing_method=None,
            trend_direction=None,
            metric_direction=metric_direction,
            slope=None,
            r_squared=None,
            quality=QualityStatus.UNAVAILABLE,
            excluded_observation_ids=excluded_ids,
            exclusion_reasons=exclusion_reasons,
        )

    if len(points) < MINIMUM_TRAJECTORY_POINTS:
        return Trajectory(
            patient_id=patient_id,
            metric_id=metric_id,
            points=points,
            smoothing_method=None,
            trend_direction=None,
            metric_direction=metric_direction,
            slope=None,
            r_squared=None,
            quality=QualityStatus.INSUFFICIENT,
            excluded_observation_ids=excluded_ids,
            exclusion_reasons=exclusion_reasons,
        )

    x_values = [float(point.period_start.toordinal()) for point in points]
    y_values = [point.raw_value for point in points]
    fit = _fit_line(x_values, y_values)
    span_days = max(x_values) - min(x_values)
    trend_direction = _classify_trend(fit.slope, span_days, y_values)

    return Trajectory(
        patient_id=patient_id,
        metric_id=metric_id,
        points=points,
        smoothing_method=_CALCULATION_METHOD,
        trend_direction=trend_direction,
        metric_direction=metric_direction,
        slope=fit.slope,
        r_squared=fit.r_squared,
        quality=QualityStatus.SUFFICIENT,
        excluded_observation_ids=excluded_ids,
        exclusion_reasons=exclusion_reasons,
    )


def estimate_domain_trajectories(
    domain: Domain,
    patient_id: str,
    observations_by_metric: dict[str, Sequence[BaselineObservation]],
    as_of: date,
) -> dict[str, Trajectory]:
    """Estimate a trajectory for every metric registered to one domain.

    A telemetry-gated metric (per
    ``analysis.registry.metrics.VERIFIED_TELEMETRY_SOURCES``) is
    classified ``UNAVAILABLE`` directly, without requiring the caller
    to supply any observations for it - mirroring
    ``analysis.baseline.engine.estimate_domain_baselines``'s handling
    of gated metrics. The returned mapping never contains a combined
    or composite "domain trajectory" - only independent per-metric
    trajectories (master spec's prohibition on a single cognitive
    score).
    """
    trajectories: dict[str, Trajectory] = {}
    for metric in metrics_for_domain(domain):
        if metric.telemetry_source not in VERIFIED_TELEMETRY_SOURCES:
            trajectories[metric.metric_id] = Trajectory(
                patient_id=patient_id,
                metric_id=metric.metric_id,
                points=(),
                smoothing_method=None,
                trend_direction=None,
                metric_direction=metric.direction,
                slope=None,
                r_squared=None,
                quality=QualityStatus.UNAVAILABLE,
                excluded_observation_ids=(),
                exclusion_reasons={},
            )
            continue
        trajectories[metric.metric_id] = estimate_trajectory(
            patient_id,
            metric.metric_id,
            observations_by_metric.get(metric.metric_id, ()),
            as_of,
        )
    return trajectories
