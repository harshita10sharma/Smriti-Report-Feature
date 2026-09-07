"""Sounds of Home analyzer (master spec S31).

Only reaction-time variability is currently computable: it uses the
verified ``response_time_ms`` column without interpreting the raw metrics
payload. Hit/miss/false-alarm rates require a confirmed target marker, and
block-decline metrics require a confirmed client-emitted block marker. The
shared ``build_result`` gate returns all of those metrics as explicit
``UNAVAILABLE`` observations until their JSONB contract is verified.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_dispersion
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _rt_sd(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
) -> MetricObservation:
    return compute_dispersion(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        extractor=lambda t: float(t.response_time_ms) if t.response_time_ms is not None else None,
    )


def _compute(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
) -> MetricObservation:
    if metric.metric_id == "sounds_home_rt_sd":
        return _rt_sd(
            metric,
            patient_id=patient_id,
            session_id=session_id,
            ts=ts,
            trials=trials,
        )
    raise AssertionError(f"unexpected verified metric for Sounds of Home: {metric.metric_id}")


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.SOUNDS_OF_HOME,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
