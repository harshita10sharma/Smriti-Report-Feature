"""Sort the Harvest analyzer (master spec S25).

switch_cost_ms is gated UNAVAILABLE: only a `post_switch` trial_context
value is documented, with no confirmed way to identify pre-switch
trials (REPORT_READINESS_AUDIT.md S4) - the master specification is
explicit that switch cost must never be computed without valid trial
context.
"""

from __future__ import annotations

from collections.abc import Sequence

from analysis.games.base import (
    GameAnalysisResult,
    build_result,
    compute_rate,
    insufficient_observations,
    observation,
)
from analysis.models.enums import GameId, QualityStatus
from analysis.models.metrics import MetricObservation
from analysis.models.telemetry import Trial
from analysis.registry.metrics import RegisteredMetric

#: Number of consecutive correct trials required to declare the
#: sorting criterion reached. This is an analytical design choice
#: (not a telemetry gap) and should be revisited once real session
#: data is available to validate it - see master spec S58 on
#: centralizing and justifying configurable thresholds.
_CRITERION_CONSECUTIVE_CORRECT = 3


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


def _trials_to_criterion(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    ordered = sorted(
        (t for t in trials if t.trial_index is not None and t.correct is not None),
        key=lambda t: t.trial_index,  # type: ignore[arg-type,return-value]
    )
    if len(ordered) < _CRITERION_CONSECUTIVE_CORRECT:
        return insufficient_observations(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, n_valid=len(ordered)
        )
    run_length = 0
    for index, trial in enumerate(ordered):
        run_length = run_length + 1 if trial.correct else 0
        if run_length >= _CRITERION_CONSECUTIVE_CORRECT:
            return observation(
                metric,
                patient_id=patient_id,
                session_id=session_id,
                ts=ts,
                value=float(index + 1),
            )
    return MetricObservation(
        metric_id=metric.metric_id,
        patient_id=patient_id,
        session_id=session_id,
        event_id=None,
        game_id=metric.game_id.value,
        value=None,
        quality=QualityStatus.UNAVAILABLE,
        unavailable_reason=(
            f"criterion of {_CRITERION_CONSECUTIVE_CORRECT} consecutive correct "
            "trials was not reached within this session"
        ),
        ts=ts,
    )


def _compute(
    metric: RegisteredMetric, *, patient_id: str, session_id: str, ts: int, trials: Sequence[Trial]
) -> MetricObservation:
    if metric.metric_id == "sort_harvest_perseverative_error_rate":
        return _perseverative_error_rate(
            metric, patient_id=patient_id, session_id=session_id, ts=ts, trials=trials
        )
    if metric.metric_id == "sort_harvest_trials_to_criterion":
        return _trials_to_criterion(
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
