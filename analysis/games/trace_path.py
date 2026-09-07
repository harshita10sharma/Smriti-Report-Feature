"""Trace the Path analyzer (master spec S26).

Only completion_ms is computable, using the verified response_time_ms
column (with the caveat, documented in the registry, that this
assumes one event per completed attempt). Variant (A/B),
stroke_velocity, lifts, jitter, and b_minus_a_ms all require fields
that are not verified columns and are gated UNAVAILABLE.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_dispersion
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    if metric.metric_id != "trace_path_completion_ms":
        raise AssertionError(f"unexpected verified metric for Trace the Path: {metric.metric_id}")
    return compute_dispersion(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        extractor=lambda t: float(t.response_time_ms) if t.response_time_ms is not None else None,
        use_median=True,
    )


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.TRACE_THE_PATH,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
