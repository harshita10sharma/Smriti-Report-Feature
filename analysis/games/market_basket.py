"""Market Basket analyzer (master spec S24).

Both span metrics require distinguishing forward from backward
trials, which has no verified column (REPORT_READINESS_AUDIT.md S4) -
so every metric registered for this game is currently gated
UNAVAILABLE. This module still exists (rather than being omitted) so
the game participates in the same dispatch mechanism as every other
game, and so this gap is visible in code, not just documentation.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _compute(metric: RegisteredMetric) -> MetricObservation:
    raise AssertionError(
        f"{metric.metric_id}: no Market Basket metric is currently verified; "
        "build_result() must never call compute() for a gated metric"
    )


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.MARKET_BASKET,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=_compute,
    )
