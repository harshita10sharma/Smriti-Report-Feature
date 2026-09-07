"""Name the Harvest analyzer (master spec S29).

No registered metric is currently computable. ``correct`` alone cannot prove
that an event represents one unique spoken item, while clusters and switches
need an unverified semantic tag. Audio remains outside this extractor because
the reference backend provides no verified event/session-to-memo association.
All registered metrics are explicitly gated until those contracts exist.
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
        f"{metric.metric_id}: no Name the Harvest metric is currently verified; "
        "build_result() must never call compute() for a gated metric"
    )


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.NAME_THE_HARVEST,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
