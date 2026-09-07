"""Lamps of the Festival analyzer (master spec S28).

sequence_error_rate/item_error_rate are computed from the verified
correct/error_class columns. Forward/backward span_achieved are gated
UNAVAILABLE - same direction-marker gap as Market Basket.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_rate
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric

_ERROR_CLASS_BY_METRIC_ID = {
    "lamps_sequence_error_rate": "sequence_error",
    "lamps_item_error_rate": "item_error",
}


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    error_value = _ERROR_CLASS_BY_METRIC_ID.get(metric.metric_id)
    if error_value is None:
        raise AssertionError(
            f"unexpected verified metric for Lamps of the Festival: {metric.metric_id}"
        )
    return compute_rate(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        is_eligible=lambda t: t.correct is False,
        is_positive=lambda t: t.error_class == error_value,
    )


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.LAMPS_OF_THE_FESTIVAL,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
