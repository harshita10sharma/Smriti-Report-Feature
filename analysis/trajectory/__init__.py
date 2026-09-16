"""Longitudinal trajectory estimation.

Consumes the same ``analysis.baseline.models.BaselineObservation``
input the personal-baseline layer uses (one session's aggregated
metric value, with session identity and calendar date) and produces
``analysis.models.trajectory.Trajectory`` - both types are reused
unchanged rather than duplicated, since "one session's evidence over
time" is the same concept whether it feeds a baseline or a
trajectory.

This package answers only "how has the observed raw value changed
over time" in neutral mathematical terms (increasing/decreasing/
stable). It never labels a patient as declining, improving,
fluctuating, or impaired - those judgments require combining a trend
with the metric's own favorability and with change-point/persistence
analysis, both left to later, not-yet-implemented phases. It also
never computes a practice-effect-adjusted value: only the raw
trajectory is produced here, exactly as
``analysis.baseline.PracticeEffectAssessment`` only exposes a raw
trajectory for the same, previously-documented reason (no verified
telemetry justifies a specific correction model yet).
"""
