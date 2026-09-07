"""Weaving Patterns analyzer (master spec S30).

All four registered metrics (mirror/rotation/detail/random error
rate) are computed from the verified correct/error_class columns.
distractor_similarity and rotation_angle are difficulty covariates,
not directional performance metrics - they have no inherent
"higher/lower is better" and are therefore intentionally not
registered as metrics at all (see
analysis/registry/game_registry.py's WEAVING_PATTERNS
difficulty_dimensions instead).
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
    error_value = metric.metric_id.removeprefix("weaving_").removesuffix("_error_rate")
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
        GameId.WEAVING_PATTERNS,
        patient_id=patient_id,
        session_id=session_id,
        ts=ts,
        trials=trials,
        compute=lambda metric: _compute(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        ),
    )
