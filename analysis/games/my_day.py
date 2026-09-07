"""My Day analyzer (master spec S27).

Only orientation_accuracy is registered, computed directly from the
verified `correct` column. Per-dimension (day/season/order/routine)
breakdown is not a registered metric at all - no verified column
carries a dimension marker.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_rate
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    if metric.metric_id != "my_day_orientation_accuracy":
        raise AssertionError(f"unexpected verified metric for My Day: {metric.metric_id}")
    return compute_rate(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        is_eligible=lambda t: t.correct is not None,
        is_positive=lambda t: bool(t.correct),
    )


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.MY_DAY,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
