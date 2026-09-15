import pytest

from analysis.domains.engine import estimate_domain
from analysis.errors import PatientIsolationError, RegistryError
from analysis.models.enums import Domain, GameId, QualityStatus
from analysis.registry import METRIC_REGISTRY, metrics_for_domain
from tests.fixtures.domain_fixtures import make_result

# --- G: SCALE SAFETY ----------------------------------------------------------


def test_incompatible_units_are_never_averaged_into_one_number() -> None:
    # VISUOSPATIAL mixes proportions (error rates) and, in the
    # registry, unbounded durations/counts - DomainEvidence must never
    # expose a single combined number for these.
    results = [
        make_result("lamps_sequence_error_rate", GameId.LAMPS_OF_THE_FESTIVAL, value=0.1),
        make_result("weaving_mirror_error_rate", GameId.WEAVING_PATTERNS, value=0.4),
    ]
    evidence = estimate_domain(Domain.VISUOSPATIAL, "p1", results)
    assert not hasattr(evidence, "value")
    assert not hasattr(evidence, "score")
    # Each metric's own value remains individually inspectable instead.
    values = {e.metric_id: e.value for e in evidence.metric_evidence}
    assert values["lamps_sequence_error_rate"] == 0.1
    assert values["weaving_mirror_error_rate"] == 0.4


def test_domain_evidence_model_has_no_composite_score_field() -> None:
    evidence = estimate_domain(Domain.MEMORY, "p1", [])
    field_names = set(type(evidence).model_fields)
    for forbidden in ("score", "value", "cognitive_score", "domain_score", "overall_score"):
        assert forbidden not in field_names


# --- H: PATIENT ISOLATION -------------------------------------------------------


def test_mismatched_patient_id_raises_patient_isolation_error() -> None:
    result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST,
        patient_id="patient-B",
    )
    with pytest.raises(PatientIsolationError):
        estimate_domain(Domain.EXECUTIVE, "patient-A", [result])


def test_two_patients_estimated_independently_do_not_contaminate() -> None:
    result_a = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST,
        patient_id="patient-a", value=0.1,
    )
    result_b = make_result(
        "sort_harvest_perseverative_error_rate", GameId.SORT_THE_HARVEST,
        patient_id="patient-b", value=0.9,
    )
    evidence_a = estimate_domain(Domain.EXECUTIVE, "patient-a", [result_a])
    evidence_b = estimate_domain(Domain.EXECUTIVE, "patient-b", [result_b])
    assert evidence_a.patient_id == "patient-a"
    assert evidence_b.patient_id == "patient-b"
    entry_a = next(e for e in evidence_a.metric_evidence if e.value is not None)
    entry_b = next(e for e in evidence_b.metric_evidence if e.value is not None)
    assert entry_a.value == 0.1
    assert entry_b.value == 0.9


# --- J: TELEMETRY GATES --------------------------------------------------------


def test_gated_metric_remains_unavailable_even_if_a_result_is_supplied_for_it() -> None:
    # sort_harvest_switch_cost_ms is telemetry-gated; even if a caller
    # mistakenly builds a "result" for it, the domain engine must
    # still treat it as gated, not trust the supplied result, because
    # it never calls into the caller's data for a non-verified metric.
    gated_result = make_result(
        "sort_harvest_switch_cost_ms", GameId.SORT_THE_HARVEST, value=999.0,
        quality=QualityStatus.SUFFICIENT,
    )
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [gated_result])
    entry = next(
        e for e in evidence.metric_evidence if e.metric_id == "sort_harvest_switch_cost_ms"
    )
    assert entry.value is None
    assert entry.quality == QualityStatus.UNAVAILABLE
    assert "telemetry_source=" in (entry.reason or "")


def test_verified_metric_with_no_supplied_result_is_unavailable_not_skipped() -> None:
    evidence = estimate_domain(Domain.EXECUTIVE, "p1", [])
    entry = next(
        e for e in evidence.metric_evidence
        if e.metric_id == "sort_harvest_perseverative_error_rate"
    )
    assert entry.quality == QualityStatus.UNAVAILABLE
    assert "no aggregation result was supplied" in (entry.reason or "")


def test_result_with_mismatched_game_id_is_rejected() -> None:
    bad_result = make_result(
        "sort_harvest_perseverative_error_rate", GameId.MY_DAY  # wrong game
    )
    with pytest.raises(RegistryError):
        estimate_domain(Domain.EXECUTIVE, "p1", [bad_result])


# --- K: REGISTRY DRIVEN ----------------------------------------------------------


def test_domain_membership_matches_the_registry_exactly() -> None:
    for domain in Domain:
        evidence = estimate_domain(domain, "p1", [])
        registered_ids = {m.metric_id for m in metrics_for_domain(domain)}
        evidence_ids = {e.metric_id for e in evidence.metric_evidence}
        assert evidence_ids == registered_ids


def test_no_metric_appears_in_the_wrong_domain() -> None:
    for domain in Domain:
        evidence = estimate_domain(domain, "p1", [])
        for entry in evidence.metric_evidence:
            assert METRIC_REGISTRY[entry.metric_id].domain == domain
