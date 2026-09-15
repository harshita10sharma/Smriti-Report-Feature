# Domain Estimation Contract

This document describes `analysis/domains/` - the layer between Phase 5's metric quality/aggregation (`analysis.aggregation`) and personal-baseline/longitudinal analysis (later, not-yet-implemented phases). It converts per-metric `AggregationResult` objects into structured, per-domain evidence. It never computes a cognitive score, a baseline, a trend, or a report state.

## The five domains

Exactly `MEMORY`, `ATTENTION`, `EXECUTIVE`, `VISUOSPATIAL`, `LANGUAGE` (`analysis.models.enums.Domain`). There is no sixth "overall cognition" domain and no composite score across domains or across a domain's own metrics.

## Registry-driven mapping

`analysis.registry.metrics_for_domain(domain)` is the single source of truth for which metrics belong to a domain - `analysis/domains/engine.py` hard-codes no second `DOMAIN_METRICS = {...}` mapping. Changing which metrics the registry assigns to a domain automatically changes what `estimate_domain` considers, with no code change required here.

## Inputs and outputs

- **Input:** `Sequence[AggregationResult]` (Phase 5's output) for whatever metrics the caller has already computed, plus a `domain` and `patient_id`.
- **Output:** `DomainEvidence` (`analysis/domains/models.py`) - one `MetricEvidenceEntry` per metric `metrics_for_domain` returns (including gated ones), plus domain-level `quality`/`reason` and coverage summaries (`usable_metric_ids`, `limited_metric_ids`, `insufficient_metric_ids`, `unavailable_metric_ids`, `usable_observation_count`, `contributing_game_ids`).

`DomainEvidence` has no numeric score field of any kind - by construction, not by convention. A UI or later phase that wants a single number must derive it itself from the structured evidence (and, per the master specification, that derivation is out of scope for this project unless explicitly authorized).

## How a metric's evidence entry is produced

For every metric `metrics_for_domain(domain)` returns:

1. **Telemetry-gated** (`telemetry_source` not in `analysis.registry.metrics.VERIFIED_TELEMETRY_SOURCES`) → `MetricEvidenceEntry` with `value=None`, `quality=UNAVAILABLE`, and a reason built from the registry's own `verification_note`. The engine never even looks for a caller-supplied result for a gated metric.
2. **Verified, but no result supplied** → also `UNAVAILABLE`, with a distinct reason ("no aggregation result was supplied for this metric") - a registered metric is never silently dropped from evidence just because the caller didn't compute it this time.
3. **Verified, with a supplied result** → the entry copies `value`, `quality`, `reason`, `source_ids`, and `valid_count` straight from the `AggregationResult`, and `direction` from the registry. Nothing is recomputed or reinterpreted.

## Directionality

Always read from the registry (`RegisteredMetric.direction`), never inferred from a metric's name, magnitude, or game. `MetricEvidenceEntry.direction` is preserved for every metric regardless of its value or quality, so a later phase can interpret "higher" or "lower" correctly without re-deriving it.

## Domain-level quality propagation

`analysis.domains.quality.classify_domain_quality` is a pure function, deterministic given only counts:

1. Zero metrics registered for the domain → `UNAVAILABLE`. (Not reachable today - every domain has at least one registered metric.)
2. No usable metrics, but at least one had some data that wasn't enough → `INSUFFICIENT`.
3. No usable metrics at all → `UNAVAILABLE`.
4. Every registered metric for the domain is usable with zero degradation (no `LIMITED`, `INSUFFICIENT`, or `UNAVAILABLE` metric anywhere in the domain) → `SUFFICIENT`.
5. Otherwise (the common case today, since every domain currently has at least one telemetry-gated metric) → `LIMITED`.

**Consequence, stated plainly:** with the registry's current telemetry gaps, no domain can reach `SUFFICIENT` today - every domain has at least one metric still pending confirmed telemetry (`CLIENT_TELEMETRY_REQUIREMENTS.md`). `LANGUAGE` specifically has zero verified metrics and will always resolve to `UNAVAILABLE` until at least one of its three metrics is confirmed. This is intentional: a domain must never appear more complete than its real evidence coverage (master spec S9.7), even at the cost of every domain currently capping out below `SUFFICIENT`.

## Missingness

An unavailable or missing metric's `value` is always `None`, never `0.0`, never a fabricated "perfect" value, and never silently excluded from `metric_evidence` - it is always present as its own entry with an explicit reason.

## Scale compatibility

Metrics with incompatible units (a proportion, a duration in ms, a count) are never averaged or combined into one number. Each stays a separate `MetricEvidenceEntry`; only `usable_observation_count` (a sum of *sample counts*, not values) aggregates across metrics, since sample counts are always commensurable regardless of what they measure.

## Provenance

Every `MetricEvidenceEntry` preserves `source_ids` and `valid_count` from its originating `AggregationResult`, plus `game_id` - so a downstream evidence builder can always answer which games/sessions/observations produced a domain's evidence.

## Patient isolation

`estimate_domain` takes `patient_id` explicitly and raises `analysis.errors.PatientIsolationError` if any supplied `AggregationResult.patient_id` disagrees with it - a defensive check, since patient scoping should already be correct by construction (every aggregation call is itself patient-scoped).

## Temporal integrity

`analysis/domains/engine.py` has no notion of "now" - like the aggregation engine beneath it, it processes exactly the `AggregationResult` objects it is given. A historical domain estimate must be built from results whose underlying observations were already filtered via `analysis.aggregation.temporal.filter_by_cutoff` before aggregation; the domain layer does not re-implement or need its own cutoff logic.

## What this phase does not do

No personal baseline, no baseline-relative normalization, no practice-effect correction, no longitudinal trend, no change detection, no persistence/concordance, no confounder or engagement analysis, no caregiver narrative, no report state, no PDF, no API, no dashboard. `DomainEvidence` is the complete output of this phase.
