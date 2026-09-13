# Metric Quality and Aggregation Contract (Phase 5)

This document describes `analysis/aggregation/` - the layer between game-specific feature extraction (Phase 4, `analysis.games`) and domain estimation (a later, not-yet-implemented phase). It answers one question only: *can a metric's contributing raw values be trusted, and how should they be combined per the registry's declared aggregation method?* It does not compute a cognitive score, a baseline, a trend, or a domain estimate.

## Inputs and outputs

- **Input:** `RawObservation` (`analysis/aggregation/models.py`) - one contributing data point: `source_id`, `ts`, and `value: float | None` (`None` means the source had no value at all - missing, not zero).
- **Output:** `AggregationResult` - the metric's aggregated `value` (or `None`), its `quality`, a human-readable `reason` (required whenever `value` is `None`, and whenever quality is degraded), `valid_count`, `missing_count`, every `excluded` observation with why it was excluded, the `source_ids` that actually contributed, and the `ts_range` they span.

Everything is driven by `analysis.registry`'s existing `RegisteredMetric` metadata (`aggregation`, `telemetry_source`, `minimum_observations`, `valid_range`) - there is no second registry.

## Supported aggregation methods

| Method | Function | Semantics |
|---|---|---|
| `MEAN` | `aggregate_mean` | Arithmetic mean of eligible values. |
| `MEDIAN` | `aggregate_median` | Median of eligible values - used for skewed timing metrics. |
| `STDDEV` | `aggregate_stddev` | Population standard deviation. Mathematically always ≥ 0. |
| `COUNT` | `aggregate_count` | Number of eligible observations - each `RawObservation` represents exactly one countable entity; the caller is responsible for only supplying one per entity it can confirm exists. |
| `MAX_ACHIEVED` | `aggregate_max_achieved` | Maximum eligible value - for span-type metrics representing the highest level actually achieved. |
| `RATE` | `aggregate_rate` | Proportion of eligible observations that are positive. Every value must be exactly `0.0` or `1.0` (a pre-confirmed eligible/positive indicator); anything else is excluded, never rounded. |
| `DIFFERENCE` | `aggregate_difference` | `summarize(after) - summarize(before)` for two explicit groups (post-switch minus pre-switch, B minus A, last block minus first block). Takes `before`/`after` sequences, not one flat list - a difference needs two named groups, never inferred from event order. |

## Quality states

Reuses the existing `QualityStatus` enum - no new status concept was introduced. `classify_quality` (`analysis/aggregation/quality.py`) is a pure function applied identically by every aggregation method:

1. **Zero candidate observations at all** → `UNAVAILABLE` ("no observations were supplied").
2. **Valid count below `metric.minimum_observations`** → `INSUFFICIENT` (even if some raw data existed - being present is not the same as being enough).
3. **Excluded+missing exceed 50% of all candidates** (`EXCESSIVE_EXCLUSION_RATIO`, `analysis/aggregation/quality.py`) even though the minimum was met → `LIMITED`. This exists so a single valid observation can never disguise a mostly-missing/invalid data window as fully trustworthy.
4. **Otherwise** → `SUFFICIENT`.

A fifth, defensive check applies after computation: if a computed value somehow falls outside `metric.valid_range` (relevant mainly for `DIFFERENCE`, whose per-value range check is intentionally skipped - see below), the result is downgraded to `LIMITED` with an explicit reason, but the value is still returned, never discarded or clipped.

`EXCESSIVE_EXCLUSION_RATIO = 0.5` is the one new configurable threshold this phase introduces. It is an engineering judgment call, not a value derived from clinical data, and should be revisited once real telemetry volume is available.

## Missingness

A missing value (`RawObservation.value is None`) is never treated as zero and never silently imputed. It is counted in `missing_count`, factored into the exclusion-ratio quality check, and otherwise excluded from every computation.

## Invalid values

If `metric.valid_range` is set, any present value outside `[min, max]` is excluded (never clipped, never coerced) and recorded in `AggregationResult.excluded` with `reason_code="outside_valid_range"` and the exact value that was rejected. `RATE`'s indicator check is a second, method-specific validity rule (`reason_code="invalid_rate_indicator"`).

`valid_range` is populated in the registry only where a metric's own semantics make a bound unambiguous: proportions get `(0.0, 1.0)`; non-negative unbounded quantities (spans, counts, durations, dispersion) get `(0.0, inf)`; a metric that is itself a difference of two bounded values (e.g. `sounds_home_block_hit_rate_decline`, a difference of two proportions) gets a symmetric bound (`(-1.0, 1.0)`). `DIFFERENCE` metrics over otherwise-unbounded quantities (`switch_cost_ms`, `b_minus_a_ms`, `block_rt_decline`) are left unbounded - a negative difference (e.g. getting faster) is meaningful, not invalid.

## Outlier policy

None. No automatic outlier removal, winsorizing, or clipping exists anywhere in this layer. The only exclusion mechanisms are the registry-declared `valid_range` and, for `RATE`, the indicator-value check - both explicit, deterministic, and fully recorded.

## Provenance

Every `AggregationResult` preserves `source_ids` (which observations contributed to `value`), `ts_range` (their timestamp span), `valid_count`/`missing_count`, and every `ExcludedObservation` (its `source_id` and why it was excluded). `patient_id` is passed explicitly by the caller on every call - never inferred - so a grouping error can never mix two patients' data.

## Sample-size policy

`minimum_observations` lives on the registry's `RegisteredMetric`, exactly as it does for Phase 4's per-session extraction - there is no separate, second threshold system. Metrics using `STDDEV` should set `minimum_observations >= 2`, since a dispersion estimate from one point is not meaningful even though the formula would return `0.0` for it.

## Unavailable-data (telemetry-gate) behavior

Every aggregation function calls `require_verified(metric)` first, which raises `AssertionError` if `metric.telemetry_source` is not `VERIFIED_COLUMN` or `DERIVED_FROM_VERIFIED_COLUMNS` (`analysis.registry.metrics.VERIFIED_TELEMETRY_SOURCES`). This mirrors the identical gate Phase 4's `analysis.games.base.require_verified` already enforces, so a metric Phase 4 correctly refuses to compute can never be silently computed here instead.

## Temporal integrity

The engine itself has no notion of "now" - it is deterministic and aggregates exactly the `RawObservation` sequence it is given. `analysis.aggregation.temporal.filter_by_cutoff(observations, cutoff_ts)` is the one canonical way for a caller building a historical report to exclude future observations before calling the engine, so later phases (longitudinal trajectories) do not each reinvent cutoff logic.
