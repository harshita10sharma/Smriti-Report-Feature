# Longitudinal Trajectory Contract

This document describes `analysis/trajectory/` - the layer between personal-baseline estimation (`analysis.baseline`) and change-point/persistence/fluctuation classification (later, not-yet-implemented phases). It answers one question only: *given a patient's history of usable observations for one metric up to a given date, how has the raw value moved over time, in purely mathematical terms?* It never labels a patient as declining, improving, fluctuating, or impaired, and it never compares a patient to anyone else.

## Reused types, not duplicated

`analysis.models.trajectory.Trajectory`/`TrajectoryPoint` already existed from the project's foundation layer as output shapes and are reused unchanged in purpose, extended only with additive provenance fields (`TrajectoryPoint.contributing_observation_ids`, `Trajectory.excluded_observation_ids`/`exclusion_reasons`) and additive movement fields (`slope`, `r_squared`, `metric_direction`), described below. The *input* shape is `analysis.baseline.models.BaselineObservation` - the same wrapper the baseline layer already uses to pair one session's `AggregationResult` with the session identity and calendar date it lacks. No second, parallel input type was created for this phase.

## Inputs and outputs

- **Input:** `Sequence[BaselineObservation]` - one entry per session, each `{session_id, observed_on, result: AggregationResult}` - for one patient and one metric.
- **Output:** `analysis.models.trajectory.Trajectory` - `points`, `smoothing_method`, `trend_direction`, `metric_direction`, `slope`, `r_squared`, `quality`, `excluded_observation_ids`, `exclusion_reasons`.

`Trajectory` has no per-domain or cross-metric field - it is always for exactly one metric. `estimate_domain_trajectories()` returns `dict[str, Trajectory]` keyed by metric id, never a combined or averaged "domain trajectory" - exactly as the specification requires (no overall cognition score, ever).

## No lookback window

Unlike `estimate_baseline()`, `estimate_trajectory()` applies no `window_days` - it considers a patient's entire verified history for the metric up to `as_of`. A trajectory is meant to show the metric's whole trend, not a fixed recent slice; the only temporal restriction is the cutoff itself.

## From observations to points

Observations are first checked for patient/metric identity (see Patient isolation, below), then filtered to `observed_on <= as_of` and sorted by `(observed_on, session_id)` for deterministic tie-breaking. Usable observations (`BaselineObservation.is_usable`) sharing a calendar day are grouped into one `TrajectoryPoint`:

- `raw_value` is the **median** of that day's usable values - a robust statistic, not a mean, consistent with the baseline layer's own choice.
- `sample_count` is the number of usable observations that day.
- `contributing_observation_ids` lists their session ids, sorted for determinism.

A calendar day with zero usable observations is never represented - there is no manufactured zero-sample point for a day with no gameplay or only excluded evidence, matching `TrajectoryPoint`'s own validator (`sample_count >= 1`, enforced structurally).

## Evidence-sufficiency rules

Configuration lives in `analysis/trajectory/config.py`, each constant documented with its purpose, units, default, and rationale:

- `MINIMUM_TRAJECTORY_POINTS = 3` - distinct-day points required before a trend may be computed at all.
- `STABLE_THRESHOLD_RATIO = 0.5` - how large a slope's total predicted change must be, relative to the trajectory's own robust variability (MAD of raw values), before it is called anything other than `STABLE`.

**These are explicit engineering defaults, not clinical thresholds** - the same caveat that applies to every constant in `analysis/baseline/config.py`, for the same reason (no real deployed telemetry exists yet to calibrate against).

`estimate_trajectory()` classifies the result as:

1. `UNAVAILABLE` - zero distinct-day points with usable evidence at all (`points == ()`).
2. `INSUFFICIENT` - some points exist, but fewer than `MINIMUM_TRAJECTORY_POINTS`. `points` is still populated (the evidence that does exist is not thrown away), but `trend_direction`/`slope`/`r_squared`/`smoothing_method` are all `None` - a slope drawn through one or two points is indistinguishable from noise or an artifact of exactly two points always forming a "perfect" line.
3. `SUFFICIENT` - the threshold is met, and a trend is fitted.

## The trend fit

`smoothing_method` is always `"ordinary_least_squares_on_daily_median"` when a trend is computed (and `None` otherwise) - it doubles as the general calculation-method label. No actual smoothing (moving average, exponential weighting) is applied; only an unweighted OLS line through the daily-median points.

The fit is pure Python (`statistics` module only - no numpy/scipy, per this project's dependency discipline) and handles the one numerical edge case that can arise: when every point has the identical raw value (zero y-variance), the standard R² formula divides by zero. This is defined explicitly as `slope=0.0, r_squared=1.0` (a flat line has no residual, so the fit is perfect by construction) rather than raising or fabricating a number. The symmetric zero-x-variance case cannot occur, because points are keyed by distinct calendar day and a trend is only fitted once at least three distinct days exist.

## Trend classification is neutral, not clinical

`trend_direction` (`analysis.models.enums.TrendDirection`: `INCREASING`/`DECREASING`/`STABLE`) is a purely mathematical description of the fitted slope's shape - never "declining", "improving", or "fluctuating". A slope is `STABLE` when its predicted total change across the observed span is smaller than `STABLE_THRESHOLD_RATIO` times the trajectory's own MAD (or whenever MAD itself is zero, since there is then no variability of any kind to call a trend); otherwise it is `INCREASING` for a positive slope or `DECREASING` for a negative one.

`metric_direction` (`analysis.models.enums.Direction`: `HIGHER_IS_BETTER`/`LOWER_IS_BETTER`) is looked up from the registry (`analysis.registry.metric_registry.METRIC_REGISTRY`) by `metric_id` and stored alongside `trend_direction` as a **separate, independent field** - never derived from or collapsed into it. An `INCREASING` trend on a `LOWER_IS_BETTER` metric (e.g. a rising error rate) is exactly as likely to be reported as a `DECREASING` trend on the same metric; this module performs no favorability interpretation of either. `metric_direction` is `None` only when `metric_id` is not registered at all.

## Quality handling and missingness

Identical policy to the baseline layer: an observation's `AggregationResult.quality` determines whether it counts. `SUFFICIENT`/`LIMITED` (`is_usable == True`) contributes to a `TrajectoryPoint`; `INSUFFICIENT`/`UNAVAILABLE` is recorded in `excluded_observation_ids` with its `AggregationResult.reason` copied into `exclusion_reasons` - never silently dropped, never treated as zero, never allowed to count toward evidence. No new `QualityStatus` value is invented; the same four values used throughout the project are reused unchanged.

## Provenance

Every `Trajectory` records exactly which session ids produced each point (`TrajectoryPoint.contributing_observation_ids`, validated to match `sample_count` whenever present) and exactly which observations were excluded and why (`Trajectory.excluded_observation_ids`/`exclusion_reasons`, validated so every excluded id has a matching reason).

## Patient isolation

`estimate_trajectory()` takes `patient_id` explicitly and raises `analysis.errors.PatientIsolationError` if any supplied observation's `AggregationResult.patient_id` disagrees - the same defensive pattern already used in `analysis.baseline.engine` and `analysis.domains.engine`. A mismatched `metric_id` raises `RegistryError` for the same reason.

## Temporal integrity

`analysis.baseline.temporal.filter_by_cutoff_date` (reused unchanged) applies the same inclusive-cutoff policy already established for baseline estimation: an observation dated after `as_of` is excluded entirely and can never influence the result. A dedicated regression test proves this using a dramatically different future value that never changes a historical trajectory.

## Domain-level trajectories

`estimate_domain_trajectories()` produces one `Trajectory` per metric registered to a domain (`analysis.registry.metrics_for_domain`). A telemetry-gated metric (per `analysis.registry.metrics.VERIFIED_TELEMETRY_SOURCES`) is classified `UNAVAILABLE` directly, without requiring the caller to supply any observations for it - mirroring `analysis.baseline.engine.estimate_domain_baselines`'s existing gating pattern. `metric_direction` is still populated for a gated metric (it is a registry fact about the metric, not a data fact about any patient), but no evidence is inspected or fabricated for it.

## What this phase does not do

No practice-effect-adjusted trajectory (only the raw trajectory is produced, exactly as `analysis.baseline.PracticeEffectAssessment` exposes only a raw trajectory, for the same reason: no verified telemetry justifies a correction model yet), no change-point detection, no sustained-change or persistence analysis, no concordance across metrics, no confounder or engagement analysis, no evidence-builder integration, no report state, no PDF, no API, no dashboard, no backend/client changes, no population normalization or z-scores, and no clinical interpretation of any kind - `INCREASING`/`DECREASING`/`STABLE` are the only labels this layer ever produces.
