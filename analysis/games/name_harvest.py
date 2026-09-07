"""Name the Harvest analyzer (master spec S29).

items_named counts trials where correct=True, on the assumption
(documented in the registry) that the tablet emits one event per
named item - this assumption itself is unverified, but the only
telemetry it uses is the verified `correct` column. clusters/switches
require a semantic-cluster tag with no verified column and are gated
UNAVAILABLE. audio_path is intentionally not a registered metric (see
analysis/registry/metric_registry.py) - it is raw evidence, not
handled by this analyzer.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_count
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    if metric.metric_id != "name_harvest_items_named":
        raise AssertionError(f"unexpected verified metric for Name the Harvest: {metric.metric_id}")
    return compute_count(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        is_eligible=lambda t: bool(t.correct),
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
