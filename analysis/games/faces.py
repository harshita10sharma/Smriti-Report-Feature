"""Faces of My Family analyzer (master spec S23).

recognition/naming/relationship/last-contact-recall accuracy are all
gated UNAVAILABLE: none of them can be isolated without a progression-
stage marker, which is not a verified column (REPORT_READINESS_AUDIT.md
S4, analysis/registry/metric_registry.py). Only the two error-class
rates are computable, from the verified `correct`/`error_class`
columns.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import GameAnalysisResult, build_result, compute_rate
from analysis.models.enums import GameId
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric


def _compute(
    metric: RegisteredMetric,
    *,
    patient_id: str,
    session_id: str,
    ts: int,
    trials: Sequence[Trial],
) -> MetricObservation:
    """Proportion of incorrect trials attributed to one error_class value.

    Only ``faces_semantic_error_rate``/``faces_random_error_rate`` ever
    reach here (the accuracy metrics are all gated); the target
    error_class value is derived from the metric_id itself so the two
    share this one implementation.
    """
    error_value = metric.metric_id.removeprefix("faces_").removesuffix("_error_rate")
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
        GameId.FACES_OF_MY_FAMILY,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
