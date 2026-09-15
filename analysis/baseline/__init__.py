"""Personal baseline and practice-effect foundation.

Consumes Phase 5's ``AggregationResult`` (one per session, for one
metric) over time and produces the typed ``analysis.models.baseline
.Baseline`` estimate already defined in the project's foundation
layer - this package implements the estimation logic, not a new
result shape.

The comparison is always PERSON vs. THEIR OWN HISTORY - there is no
population norm and no cross-patient comparison anywhere in this
package. Baseline-relative normalization, longitudinal trend
estimation, and change detection are later, not-yet-implemented
stages; this package only establishes whether enough personal history
exists to trust a center/variability estimate at all.

Practice-effect correction is not implemented here: no verified
telemetry currently justifies a specific correction model (no game
emits confirmed item-repetition or exposure-count data). This package
instead exposes the ordered raw trajectory as the extension point a
later phase can build an actual correction against, per
``analysis.baseline.models.PracticeEffectAssessment``.
"""
