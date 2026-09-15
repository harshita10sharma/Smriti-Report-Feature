from analysis.domains.engine import estimate_domain
from analysis.models.enums import Domain, GameId, QualityStatus
from tests.fixtures.domain_fixtures import make_result

# --- A: EMPTY DOMAIN --------------------------------------------------------


def test_no_observations_produces_explicit_unavailable_result() -> None:
    evidence = estimate_domain(Domain.LANGUAGE, "p1", [])
    assert evidence.quality == QualityStatus.UNAVAILABLE
    assert evidence.reason is not None
    assert evidence.usable_metric_ids == ()
    # every registered language metric is present as evidence, just unavailable
    assert evidence.total_registered_domain_metrics == 3
    assert set(evidence.unavailable_metric_ids) == {
        m.metric_id for m in evidence.metric_evidence
    }


def test_empty_domain_never_fabricates_a_value() -> None:
    evidence = estimate_domain(Domain.LANGUAGE, "p1", [])
    for entry in evidence.metric_evidence:
        assert entry.value is None


# --- B: SINGLE VALID METRIC --------------------------------------------------


def test_single_valid_metric_produces_correct_evidence() -> None:
    result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST, value=0.25
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [result])
    assert evidence.domain == Domain.EXECUTIVE
    assert evidence.patient_id == "p1"
    assert "sort_harvest_perseverative_error_rate" in evidence.usable_metric_ids
    matching = [
        e for e in evidence.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    ]
    assert matching[0].value == 0.25
    assert matching[0].game_id == GameId.SORT_THE_HARVEST


# --- C: MULTIPLE METRICS -----------------------------------------------------


def test_multiple_contributing_metrics_are_all_preserved_without_double_counting() -> None:
    results = [
        make_result("lamps_sequence_error_rate", GameId.LAMPS_OF_THE_FESTIVAL, value=0.1),
        make_result("lamps_item_error_rate", GameId.LAMPS_OF_THE_FESTIVAL, value=0.2),
        make_result("weaving_mirror_error_rate", GameId.WEAVING_PATTERNS, value=0.3),
    ]
    evidence = estimate_domain(Domain.VISUOSPATIAL, "p1", results)
    assert set(evidence.usable_metric_ids) == {
        "lamps_sequence_error_rate",
        "lamps_item_error_rate",
        "weaving_mirror_error_rate",
    }
    # each metric_id appears exactly once in metric_evidence
    ids = [e.metric_id for e in evidence.metric_evidence]
    assert len(ids) == len(set(ids))
    assert {GameId.LAMPS_OF_THE_FESTIVAL, GameId.WEAVING_PATTERNS} == set(
        evidence.contributing_game_ids
    )


def test_results_for_other_domains_are_ignored_not_double_counted() -> None:
    # my_day_orientation_accuracy belongs to MEMORY, not EXECUTIVE.
    unrelated = make_result("my_day_orientation_accuracy", GameId.MY_DAY, value=0.9)
    executive_result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST, value=0.1
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [unrelated, executive_result])
    assert "my_day_orientation_accuracy" not in {e.metric_id for e in evidence.metric_evidence}
    assert evidence.usable_metric_ids == ("sort_harvest_perseverative_error_rate",)


# --- I: PROVENANCE ------------------------------------------------------------


def test_provenance_survives_domain_estimation() -> None:
    result = make_result(
        "sort_harvest_perseverative_error_rate",
        GameId.SORT_THE_HARVEST,
        source_ids=("event-a", "event-b"),
        valid_count=2,
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [result])
    entry = next(
        e for e in evidence.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    )
    assert entry.source_ids == ("event-a", "event-b")
    assert entry.valid_count == 2
    assert entry.game_id == GameId.SORT_THE_HARVEST


def test_usable_observation_count_sums_only_usable_metrics() -> None:
    usable = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST, valid_count=7
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [usable])
    # 3 other executive metrics are gated/unavailable and contribute 0
    assert evidence.usable_observation_count == 7
