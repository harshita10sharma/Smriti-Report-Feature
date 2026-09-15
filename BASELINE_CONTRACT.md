# Personal Baseline and Practice-Effect Contract

This document describes `analysis/baseline/` - the layer between domain estimation (`analysis.domains`) and personal-baseline-relative normalization/longitudinal trend analysis (later, not-yet-implemented phases). It answers one question only: *given a patient's history of session-level results for one metric, is there enough of their own repeated evidence to trust a personal baseline, and if so, what is it?* It never compares a patient to anyone else, and it does not yet normalize, detect trends, or detect change.

## Reused types, not duplicated

`analysis.models.baseline.Baseline` (the estimate itself) already existed from the project's foundation layer and is reused unchanged in shape, extended only with one additive field (`contributing_observation_ids`, described below). This package adds only what was genuinely missing: the *input* shape (`BaselineObservation`, pairing one session's `AggregationResult` with the session identity and calendar date it lacks) and the estimation logic itself.

## Inputs and outputs

- **Input:** `Sequence[BaselineObservation]` - one entry per session, each `{session_id, observed_on, result: AggregationResult}` - for one patient and one metric.
- **Output:** `analysis.models.baseline.Baseline` - `status`, `period_start`/`period_end`, `n_sessions`, `n_days`, `center`, `variability`, `contributing_observation_ids`, `excluded_observation_ids`, `exclusion_reasons`.

`Baseline` has no per-domain or cross-metric field - it is always for exactly one metric, exactly as the specification requires (no overall cognition score, ever).

## Baseline eligibility rules

Configuration lives in `analysis/baseline/config.py`, each constant documented with its purpose, units, default, and rationale:

- `BASELINE_WINDOW_DAYS = 28` - how far back from the report's "as of" date the engine looks for evidence at all.
- `MINIMUM_BASELINE_SESSIONS = 5` - usable sessions required before a baseline may become `ESTABLISHED`.
- `MINIMUM_BASELINE_DAYS = 5` - distinct calendar days those sessions must span, so several sessions played in one sitting cannot alone establish a baseline.

**These are explicit engineering defaults, not clinical thresholds.** No real deployed telemetry exists yet for this project to calibrate against (per `REPORT_READINESS_AUDIT.md` and the client-repository reconciliation - only one of nine games has any client implementation at all today). They are expected to be revisited once real session-density data exists.

`estimate_baseline()` classifies the result as:
1. `INSUFFICIENT_DATA` - zero usable observations in the window.
2. `ESTABLISHING` - some usable observations exist, but below `MINIMUM_BASELINE_SESSIONS` or `MINIMUM_BASELINE_DAYS`.
3. `ESTABLISHED` - both thresholds met. `center` is the median and `variability` the median absolute deviation (MAD) of the usable values - robust statistics, not an assumed-Gaussian mean/stddev, per the specification's explicit caution against assuming normality.

A single session, or several sessions on one day, can never reach `ESTABLISHED` regardless of how good the data looks.

## Quality handling

An observation's `AggregationResult.quality` determines whether it counts:

- `SUFFICIENT` or `LIMITED` (`BaselineObservation.is_usable == True`) → contributes its value to `center`/`variability` and counts toward `n_sessions`/`n_days`.
- `INSUFFICIENT` or `UNAVAILABLE` → recorded in `excluded_observation_ids` with its own `AggregationResult.reason` copied into `exclusion_reasons` - never silently dropped, never treated as zero, never allowed to count toward evidence.

No quality state is invented here - the same four `QualityStatus` values used throughout the project (`analysis.aggregation.quality`, `analysis.domains.quality`) are reused unchanged.

## Missingness

A missing or unavailable metric value never becomes `0.0`, never becomes the mean of other values, and is never silently imputed. It is excluded, with a reason, exactly as described above.

## Provenance

Every `Baseline` records exactly which session ids produced its estimate (`contributing_observation_ids`, required and validated non-empty whenever `status == ESTABLISHED`) and exactly which were excluded and why (`excluded_observation_ids`/`exclusion_reasons`). `period_start`/`period_end` reflect the actual earliest/latest contributing date, not the nominal window bounds - a baseline never claims a longer observed period than it actually has.

## Patient isolation

`estimate_baseline()` and `assess_practice_effect()` both take `patient_id` explicitly and raise `analysis.errors.PatientIsolationError` if any supplied observation's `AggregationResult.patient_id` disagrees - the same defensive pattern already used in `analysis.domains.engine`. A mismatched `metric_id` raises `RegistryError` for the same reason.

## Temporal integrity

`analysis.baseline.temporal.filter_by_cutoff_date` applies the same inclusive-cutoff policy as `analysis.aggregation.temporal.filter_by_cutoff`, re-expressed for `BaselineObservation.observed_on` (a calendar date) since `AggregationResult` carries no scalar timestamp of its own. `estimate_baseline()` additionally enforces the lower window bound (`as_of - BASELINE_WINDOW_DAYS`). An observation dated after `as_of` is excluded from the window entirely and can never influence the result - proven by a dedicated regression test using a dramatically different future value.

## Practice-effect foundation - intentionally incomplete

`assess_practice_effect()` and `PracticeEffectAssessment` exist to expose the ordered, unmodified raw trajectory of a metric's usable values over time. **No correction is computed.** `PracticeEffectAssessment.correction_applied` is structurally forced to `False` by a model validator - it cannot be set to `True` today. This is deliberate: no game currently has verified telemetry (e.g. confirmed item-repetition or exposure-count data) that would justify a specific learning-curve or practice-effect correction model. Inventing one now would mean fabricating a statistical claim this project has no evidence for. The raw trajectory this function exposes is the extension point a later phase can build a real correction against, once such telemetry is confirmed.

## What this phase does not do

No baseline-relative normalization (z-scores or otherwise), no population comparison, no longitudinal trend/slope estimation, no change-point detection, no persistence/concordance, no confounder or engagement analysis, no actual practice-effect correction, no report state, no PDF, no API, no dashboard, and no clinical interpretation of any kind.
