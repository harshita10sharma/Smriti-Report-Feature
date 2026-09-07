"""Trace the Path analyzer (master spec S26).

No registered metric is currently computable. ``response_time_ms`` is a
verified column, but no verified event field establishes that it represents a
completed whole-task attempt. Variant, completion, and motor telemetry remain
explicitly gated pending a verified JSONB contract.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    raise AssertionError(
        f"{metric.metric_id}: no Trace the Path metric is currently verified; "
        "build_result() must never call compute() for a gated metric"
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
