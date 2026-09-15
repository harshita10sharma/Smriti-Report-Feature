"""Domain estimation (master spec S4-S13).

Converts validated, quality-controlled metric evidence (Phase 5's
``AggregationResult`` per metric) into structured, per-domain evidence
for each of the five independent cognitive domains: memory, attention,
executive, visuospatial, language.

This package never produces an overall cognitive score, a brain score,
or any weighted composite across domains or across metrics with
incompatible scales - see ``analysis.domains.models.DomainEvidence``,
which exposes per-metric evidence and coverage counts, never a single
domain number. Personal baseline, normalization, and longitudinal
analysis are later phases and are not implemented here.

Domain membership is entirely driven by ``analysis.registry
.metrics_for_domain`` - this package hard-codes no second
game/metric-to-domain mapping.
"""
