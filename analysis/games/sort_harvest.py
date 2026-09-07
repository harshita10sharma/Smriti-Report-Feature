"""Sort the Harvest analyzer (master spec S25).

Switch cost and trials to criterion are gated ``UNAVAILABLE``. Although
``trial_context='post_switch'`` is documented, no verified field identifies
the pre-switch comparison set or separates the trials belonging to each
rule. The analyzer therefore computes only the defensible perseverative-error
rate and never infers a rule switch from trial order.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_rate
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _perseverative_error_rate(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    return compute_rate(
        metric,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        is_eligible=lambda t: t.correct is not None,
        is_positive=lambda t: t.error_class == "perseverative",
    )


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    if metric.metric_id == "sort_harvest_perseverative_error_rate":
        return _perseverative_error_rate(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        )
    raise AssertionError(f"unexpected verified metric for Sort the Harvest: {metric.metric_id}")


def analyze(
    patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> GameAnalysisResult:
    return build_result(
        GameId.SORT_THE_HARVEST,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
