from analysis.aggregation.engine import aggregate_rate
from analysis.aggregation.models import RawObservation
from analysis.aggregation.temporal import filter_by_cutoff
from analysis.domains.engine import estimate_all_domains, estimate_domain
from analysis.models.enums import Domain, GameId
from analysis.registry import METRIC_REGISTRY
from tests.fixtures.domain_fixtures import make_result

# --- L: TEMPORAL INTEGRITY ------------------------------------------------------


def test_future_observation_cannot_influence_a_historical_domain_result() -> None:
    metric = METRIC_REGISTRY["sort_harvest_perseverative_error_rate"]
    historical = [
        RawObservation(source_id="e1", ts=0, value=0.0),
        RawObservation(source_id="e2", ts=1, value=0.0),
    ]
    future_event = RawObservation(source_id="future", ts=1000, value=1.0)

    filtered = filter_by_cutoff([*historical, future_event], cutoff_ts=1)
    result_with_future_filtered = aggregate_rate(metric, "p1", filtered)
    result_without_future_at_all = aggregate_rate(metric, "p1", historical)

    evidence_filtered = estimate_domain(
        Domain.EXECUTIVE, "p1", [result_with_future_filtered]
    )
    evidence_no_future = estimate_domain(
        Domain.EXECUTIVE, "p1", [result_without_future_at_all]
    )

    entry_filtered = next(
        e for e in evidence_filtered.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    )
    entry_no_future = next(
        e for e in evidence_no_future.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    )
    assert entry_filtered.value == entry_no_future.value == 0.0


def test_unfiltered_future_observation_would_have_changed_the_result() -> None:
    # Sanity check that the future event genuinely mattered - confirms
    # the previous test exercises real protection, not a no-op.
    metric = METRIC_REGISTRY["sort_harvest_perseverative_error_rate"]
    historical = [
        RawObservation(source_id="e1", ts=0, value=0.0),
        RawObservation(source_id="e2", ts=1, value=0.0),
    ]
    future_event = RawObservation(source_id="future", ts=1000, value=1.0)

    unfiltered_result = aggregate_rate(metric, "p1", [*historical, future_event])
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [unfiltered_result])
    entry = next(
        e for e in evidence.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    )
    assert entry.value != 0.0


# --- M: DETERMINISM --------------------------------------------------------------


def test_identical_input_produces_identical_domain_evidence() -> None:
    results = [
        make_result("lamps_sequence_error_rate", GameId.LAMPS_OF_THE_FESTIVAL, value=0.2),
        make_result("weaving_mirror_error_rate", GameId.WEAVING_PATTERNS, value=0.4),
    ]
    first = estimate_domain(Domain.VISUOSPATIAL, "p1", results)
    second = estimate_domain(Domain.VISUOSPATIAL, "p1", results)
    assert first == second


def test_estimate_all_domains_is_deterministic_and_covers_all_five() -> None:
    results = [
        make_result("sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST, value=0.1),
    ]
    first = estimate_all_domains("p1", results)
    second = estimate_all_domains("p1", results)
    assert set(first) == set(Domain) == set(second)
    for domain in Domain:
        assert first[domain] == second[domain]


def test_estimate_all_domains_does_not_cross_contaminate_between_domains() -> None:
    results = [
        make_result("sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST, value=0.1),
        make_result("my_day_orientation_accuracy", GameId.MY_DAY, value=0.9),
    ]
    all_domains = estimate_all_domains("p1", results)
    executive_ids = {e.metric_id for e in all_domains[Domain.EXECUTIVE].metric_evidence}
    memory_ids = {e.metric_id for e in all_domains[Domain.MEMORY].metric_evidence}
    assert "my_day_orientation_accuracy" not in executive_ids
    assert "sort_harvest_perseverative_error_rate" not in memory_ids
