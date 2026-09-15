"""Personal baseline and practice-effect-foundation estimation.

``estimate_baseline`` is the one function that turns a patient's
session-by-session ``BaselineObservation`` history for one metric into
the existing ``analysis.models.baseline.Baseline`` estimate. It never
compares a patient to anyone else, never normalizes against a
population, and never fabricates a value for a window with too little
evidence.
"""

from __future__ import annotations

import statistics
from collections.abc import Sequence
from datetime import date, timedelta

from analysis.baseline.config import (
    BASELINE_WINDOW_DAYS,
    MINIMUM_BASELINE_DAYS,
    MINIMUM_BASELINE_SESSIONS,
)
from analysis.baseline.models import (
    BaselineObservation,
    PracticeEffectAssessment,
    PracticeObservationPoint,
)
from analysis.baseline.temporal import filter_by_cutoff_date
from analysis.errors import PatientIsolationError, RegistryError
from analysis.models.baseline import Baseline
from analysis.models.enums import BaselineStatus, Domain, QualityStatus
from analysis.registry import metrics_for_domain
from analysis.registry.metrics import VERIFIED_TELEMETRY_SOURCES


def _validated_window(
    patient_id: str,
    metric_id: str,
    observations: Sequence[BaselineObservation],
    as_of: date,
    window_days: int,
) -> list[BaselineObservation]:
    """Check patient/metric identity, then return observations within
    ``[as_of - window_days, as_of]``, ordered by date.

    Raises ``PatientIsolationError``/``RegistryError`` for a caller
    contract violation (wrong patient's or wrong metric's data
    supplied) - defensive checks that should never trigger if callers
    scope their queries correctly.
    """
    for obs in observations:
        if obs.result.patient_id != patient_id:
            raise PatientIsolationError(
                f"{metric_id}: observation for session {obs.session_id!r} belongs "
                f"to patient {obs.result.patient_id!r}, but baseline estimation was "
                f"requested for patient {patient_id!r}"
            )
        if obs.result.metric_id != metric_id:
            raise RegistryError(
                f"observation for session {obs.session_id!r} is for metric "
                f"{obs.result.metric_id!r}, but baseline estimation was requested "
                f"for metric {metric_id!r}"
            )

    window_start = as_of - timedelta(days=window_days)
    within_window = [obs for obs in observations if window_start <= obs.observed_on]
    return sorted(filter_by_cutoff_date(within_window, cutoff=as_of), key=lambda o: o.observed_on)


def _median_absolute_deviation(values: Sequence[float]) -> float:
    """Robust dispersion estimate (master spec S38: "do not blindly
    assume Gaussian distributions"; MAD is explicitly suggested)."""
    center = statistics.median(values)
    return statistics.median(abs(value - center) for value in values)


def estimate_baseline(
    patient_id: str,
    metric_id: str,
    observations: Sequence[BaselineObservation],
    as_of: date,
    window_days: int = BASELINE_WINDOW_DAYS,
) -> Baseline:
    """Estimate a personal baseline for one patient/metric as of a date.

    Only observations with ``window_start <= observed_on <= as_of``
    (inclusive both ends) are considered - nothing outside the window
    is inspected at all, so a future session can never influence a
    historical baseline (master spec S29).

    Within the window, an observation with ``is_usable`` False
    (quality INSUFFICIENT or UNAVAILABLE) is recorded in
    ``excluded_observation_ids``/``exclusion_reasons`` rather than
    silently dropped or treated as zero. The baseline reaches
    ``ESTABLISHED`` only when at least ``MINIMUM_BASELINE_SESSIONS``
    usable observations exist, spanning at least
    ``MINIMUM_BASELINE_DAYS`` distinct calendar days - otherwise it is
    ``ESTABLISHING`` (evidence exists but is not yet enough) or
    ``INSUFFICIENT_DATA`` (no usable evidence at all in the window).
    """
    windowed = _validated_window(patient_id, metric_id, observations, as_of, window_days)

    usable = [obs for obs in windowed if obs.is_usable]
    excluded = [obs for obs in windowed if not obs.is_usable]
    excluded_ids = tuple(obs.session_id for obs in excluded)
    exclusion_reasons = {
        obs.session_id: (obs.result.reason or "no reason recorded") for obs in excluded
    }

    n_sessions = len(usable)
    n_days = len({obs.observed_on for obs in usable})

    if n_sessions == 0:
        return Baseline(
            patient_id=patient_id,
            metric_id=metric_id,
            status=BaselineStatus.INSUFFICIENT_DATA,
            period_start=None,
            period_end=None,
            n_sessions=0,
            n_days=0,
            center=None,
            variability=None,
            contributing_observation_ids=(),
            excluded_observation_ids=excluded_ids,
            exclusion_reasons=exclusion_reasons,
        )

    if n_sessions < MINIMUM_BASELINE_SESSIONS or n_days < MINIMUM_BASELINE_DAYS:
        return Baseline(
            patient_id=patient_id,
            metric_id=metric_id,
            status=BaselineStatus.ESTABLISHING,
            period_start=None,
            period_end=None,
            n_sessions=n_sessions,
            n_days=n_days,
            center=None,
            variability=None,
            contributing_observation_ids=(),
            excluded_observation_ids=excluded_ids,
            exclusion_reasons=exclusion_reasons,
        )

    values = [obs.result.value for obs in usable if obs.result.value is not None]
    dates = [obs.observed_on for obs in usable]
    return Baseline(
        patient_id=patient_id,
        metric_id=metric_id,
        status=BaselineStatus.ESTABLISHED,
        period_start=min(dates),
        period_end=max(dates),
        n_sessions=n_sessions,
        n_days=n_days,
        center=statistics.median(values),
        variability=_median_absolute_deviation(values),
        contributing_observation_ids=tuple(obs.session_id for obs in usable),
        excluded_observation_ids=excluded_ids,
        exclusion_reasons=exclusion_reasons,
    )


def estimate_domain_baselines(
    domain: Domain,
    patient_id: str,
    observations_by_metric: dict[str, Sequence[BaselineObservation]],
    as_of: date,
    window_days: int = BASELINE_WINDOW_DAYS,
) -> dict[str, Baseline]:
    """Estimate a baseline for every metric registered to one domain.

    A telemetry-gated metric (per
    ``analysis.registry.metrics.VERIFIED_TELEMETRY_SOURCES``) is
    classified ``INSUFFICIENT_DATA`` directly, without requiring the
    caller to supply any observations for it - mirroring
    ``analysis.domains.engine.estimate_domain``'s handling of gated
    metrics.
    """
    baselines: dict[str, Baseline] = {}
    for metric in metrics_for_domain(domain):
        if metric.telemetry_source not in VERIFIED_TELEMETRY_SOURCES:
            baselines[metric.metric_id] = Baseline(
                patient_id=patient_id,
                metric_id=metric.metric_id,
                status=BaselineStatus.INSUFFICIENT_DATA,
                period_start=None,
                period_end=None,
                n_sessions=0,
                n_days=0,
                center=None,
                variability=None,
                contributing_observation_ids=(),
                excluded_observation_ids=(),
                exclusion_reasons={},
            )
            continue
        baselines[metric.metric_id] = estimate_baseline(
            patient_id,
            metric.metric_id,
            observations_by_metric.get(metric.metric_id, ()),
            as_of,
            window_days,
        )
    return baselines


def assess_practice_effect(
    patient_id: str,
    metric_id: str,
    observations: Sequence[BaselineObservation],
    as_of: date,
    window_days: int = BASELINE_WINDOW_DAYS,
) -> PracticeEffectAssessment:
    """Expose the ordered raw trajectory for a metric, with no
    correction applied (see ``PracticeEffectAssessment``'s docstring
    for why: no verified telemetry currently justifies a specific
    practice-effect correction model).

    Reuses ``MINIMUM_BASELINE_SESSIONS`` as the evidence threshold -
    below it, the trajectory is too short to be useful to any later
    correction model, and the assessment is ``INSUFFICIENT``.
    """
    windowed = _validated_window(patient_id, metric_id, observations, as_of, window_days)
    usable = [obs for obs in windowed if obs.is_usable]

    if len(usable) < MINIMUM_BASELINE_SESSIONS:
        return PracticeEffectAssessment(
            patient_id=patient_id,
            metric_id=metric_id,
            status=QualityStatus.INSUFFICIENT,
            reason=(
                f"only {len(usable)} usable observation(s) in the window; "
                f"minimum_sessions={MINIMUM_BASELINE_SESSIONS}"
            ),
            raw_trajectory=(),
            correction_applied=False,
        )

    trajectory = tuple(
        PracticeObservationPoint(
            session_id=obs.session_id, observed_on=obs.observed_on, value=obs.result.value
        )
        for obs in usable
        if obs.result.value is not None
    )
    return PracticeEffectAssessment(
        patient_id=patient_id,
        metric_id=metric_id,
        status=QualityStatus.SUFFICIENT,
        reason=None,
        raw_trajectory=trajectory,
        correction_applied=False,
    )
