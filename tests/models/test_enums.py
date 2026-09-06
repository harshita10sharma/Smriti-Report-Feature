from analysis.models.enums import (
    ChangeType,
    Direction,
    Domain,
    EvidenceSeverity,
    GameId,
    MetricType,
    QualityStatus,
    ReportStatus,
)


def test_exactly_five_domains_no_overall_score() -> None:
    domains = {member.value for member in Domain}
    assert domains == {
        "memory",
        "attention",
        "executive",
        "visuospatial",
        "language",
    }


def test_exactly_nine_canonical_games() -> None:
    games = {member.value for member in GameId}
    assert games == {
        "faces_of_my_family",
        "market_basket",
        "sort_the_harvest",
        "trace_the_path",
        "my_day",
        "lamps_of_the_festival",
        "name_the_harvest",
        "weaving_patterns",
        "sounds_of_home",
    }


def test_report_status_has_no_diagnostic_values() -> None:
    forbidden_substrings = ("dementia", "alzheimer", "mci", "diagnos")
    for status in ReportStatus:
        lowered = status.value.lower()
        for forbidden in forbidden_substrings:
            assert forbidden not in lowered


def test_direction_has_exactly_two_values() -> None:
    assert {member.value for member in Direction} == {
        "higher_is_better",
        "lower_is_better",
    }


def test_metric_type_has_three_categories() -> None:
    assert len(list(MetricType)) == 3


def test_quality_status_distinguishes_insufficient_from_unavailable() -> None:
    values = {member.value for member in QualityStatus}
    assert "insufficient" in values
    assert "unavailable" in values
    assert len(values) == 4


def test_evidence_severity_has_three_levels() -> None:
    assert len(list(EvidenceSeverity)) == 3


def test_change_type_distinguishes_fluctuating_from_abrupt() -> None:
    values = {member.value for member in ChangeType}
    assert "fluctuating" in values
    assert "abrupt_change" in values
    assert values != {"gradual_change", "abrupt_change"}
