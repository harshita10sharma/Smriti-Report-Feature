from analysis.domains.engine import estimate_domain
from analysis.models.enums import Direction, Domain, GameId, QualityStatus
from analysis.registry import METRIC_REGISTRY
from tests.fixtures.domain_fixtures import make_result

# --- D: MIXED QUALITY --------------------------------------------------------


def test_sufficient_plus_limited_yields_domain_limited() -> None:
    results = [
        make_result(
            "lamps_sequence_error_rate", GameId.LAMPS_OF_THE_FESTIVAL,
            quality=QualityStatus.SUFFICIENT,
        ),
        make_result(
            "lamps_item_error_rate", GameId.LAMPS_OF_THE_FESTIVAL,
            quality=QualityStatus.LIMITED, reason="degraded",
        ),
        make_result(
            "weaving_mirror_error_rate", GameId.WEAVING_PATTERNS,
            quality=QualityStatus.SUFFICIENT,
        ),
        make_result(
            "weaving_rotation_error_rate", GameId.WEAVING_PATTERNS,
            quality=QualityStatus.SUFFICIENT,
        ),
        make_result(
            "weaving_detail_error_rate", GameId.WEAVING_PATTERNS,
            quality=QualityStatus.SUFFICIENT,
        ),
        make_result(
            "weaving_random_error_rate", GameId.WEAVING_PATTERNS,
            quality=QualityStatus.SUFFICIENT,
        ),
    ]
    evidence = estimate_domain(Domain.VISUOSPATIAL, "p1", results)
    assert evidence.quality == QualityStatus.LIMITED
    assert "lamps_item_error_rate" in evidence.limited_metric_ids


def test_sufficient_plus_unavailable_yields_domain_limited_not_sufficient() -> None:
    # Only 1 of 4 EXECUTIVE metrics is ever verified, so this is really
    # exercising the always-partial-coverage case.
    result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST,
        quality=QualityStatus.SUFFICIENT,
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [result])
    assert evidence.quality == QualityStatus.LIMITED


def test_insufficient_plus_unavailable_yields_domain_insufficient() -> None:
    result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST,
        value=None, quality=QualityStatus.INSUFFICIENT,
        reason="not enough trials",
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [result])
    assert evidence.quality == QualityStatus.INSUFFICIENT
    assert "sort_harvest_perseverative_error_rate" in evidence.insufficient_metric_ids


def test_quality_propagation_is_deterministic_regardless_of_result_order() -> None:
    results_a = [
        make_result("lamps_sequence_error_rate", GameId.LAMPS_OF_THE_FESTIVAL),
        make_result("weaving_mirror_error_rate", GameId.WEAVING_PATTERNS),
    ]
    results_b = list(reversed(results_a))
    evidence_a = estimate_domain(Domain.VISUOSPATIAL, "p1", results_a)
    evidence_b = estimate_domain(Domain.VISUOSPATIAL, "p1", results_b)
    assert evidence_a.quality == evidence_b.quality
    assert set(evidence_a.usable_metric_ids) == set(evidence_b.usable_metric_ids)


# --- E: MISSINGNESS -----------------------------------------------------------


def test_unavailable_metric_is_not_a_perfect_score() -> None:
    evidence = estimate_domain(Domain.LANGUAGE, "p1", [])
    for entry in evidence.metric_evidence:
        assert entry.value is None
        assert entry.value != 0.0
        assert entry.value != 1.0


def test_missing_metric_does_not_inflate_usable_observation_count() -> None:
    evidence = estimate_domain(Domain.LANGUAGE, "p1", [])
    assert evidence.usable_observation_count == 0


# --- F: DIRECTIONALITY ---------------------------------------------------------


def test_higher_is_better_direction_is_preserved() -> None:
    result = make_result("my_day_orientation_accuracy", GameId.MY_DAY, value=0.9)
    evidence = estimate_domain(Domain.MEMORY, "p1", [result])
    entry = next(
        e for e in evidence.metric_evidence if e.metric_id == "my_day_orientation_accuracy"
    )
    assert entry.direction == Direction.HIGHER_IS_BETTER


def test_lower_is_better_direction_is_preserved() -> None:
    result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST, value=0.1
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [result])
    entry = next(
        e for e in evidence.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    )
    assert entry.direction == Direction.LOWER_IS_BETTER


def test_direction_always_comes_from_the_registry_not_inference() -> None:
    result = make_result("my_day_orientation_accuracy", GameId.MY_DAY, value=0.1)  # low value
    evidence = estimate_domain(Domain.MEMORY, "p1", [result])
    entry = next(
        e for e in evidence.metric_evidence if e.metric_id == "my_day_orientation_accuracy"
    )
    # Direction must match the registry regardless of the observed value.
    assert entry.direction == METRIC_REGISTRY["my_day_orientation_accuracy"].direction
