from analysis.models.enums import ValidationSeverity
from analysis.telemetry.validation import validate_batch, validate_event
from tests.fixtures.telemetry_fixtures import (
    duplicate_event_batch,
    incomplete_event,
    malformed_event,
    negative_duration_event,
    undocumented_error_class_event,
    unknown_game_event,
    valid_event,
)


def test_valid_event_is_accepted_with_no_issues() -> None:
    event, issues = validate_event(valid_event())
    assert event is not None
    assert issues == ()


def test_incomplete_event_missing_domain_is_rejected() -> None:
    event, issues = validate_event(incomplete_event())
    assert event is None
    assert any(issue.code == "structural_validation_error" for issue in issues)
    assert all(issue.severity == ValidationSeverity.ERROR for issue in issues)


def test_malformed_event_wrong_type_is_rejected() -> None:
    event, issues = validate_event(malformed_event())
    assert event is None
    assert any(issue.code == "structural_validation_error" for issue in issues)


def test_unknown_game_id_is_rejected_not_guessed() -> None:
    event, issues = validate_event(unknown_game_event())
    assert event is None
    assert any(issue.code == "unknown_game_id" for issue in issues)


def test_negative_duration_is_rejected() -> None:
    event, issues = validate_event(negative_duration_event())
    assert event is None
    assert any(issue.code == "impossible_negative_duration" for issue in issues)


def test_undocumented_error_class_is_a_warning_not_a_rejection() -> None:
    event, issues = validate_event(undocumented_error_class_event())
    assert event is not None
    assert len(issues) == 1
    assert issues[0].severity == ValidationSeverity.WARNING
    assert issues[0].code == "undocumented_error_class_value"


def test_non_positive_timestamp_is_rejected() -> None:
    event, issues = validate_event(valid_event(ts=0))
    assert event is None
    assert any(issue.code == "invalid_timestamp" for issue in issues)


def test_non_finite_difficulty_is_rejected() -> None:
    event, issues = validate_event(valid_event(item_difficulty=float("nan")))
    assert event is None
    assert any(issue.code == "invalid_difficulty" for issue in issues)


def test_negative_trial_index_is_rejected() -> None:
    event, issues = validate_event(valid_event(trial_index=-1))
    assert event is None
    assert any(issue.code == "impossible_negative_value" for issue in issues)


def test_negative_hint_level_is_rejected() -> None:
    event, issues = validate_event(valid_event(hint_level=-1))
    assert event is None
    assert any(
        issue.code == "impossible_negative_value" and issue.field == "hint_level"
        for issue in issues
    )


def test_undocumented_trial_context_is_a_warning_not_a_rejection() -> None:
    event, issues = validate_event(valid_event(trial_context="an_undocumented_stage"))
    assert event is not None
    assert len(issues) == 1
    assert issues[0].severity == ValidationSeverity.WARNING
    assert issues[0].code == "undocumented_trial_context_value"


class TestValidateBatch:
    def test_all_valid_events_are_kept(self) -> None:
        report = validate_batch([valid_event(id="a"), valid_event(id="b")])
        assert report.usable_count == 2
        assert report.dropped_count == 0
        assert report.total_input_count == 2

    def test_duplicate_event_ids_reject_the_second_occurrence(self) -> None:
        report = validate_batch(duplicate_event_batch())
        assert report.usable_count == 1
        assert report.dropped_count == 1
        assert report.data_quality_summary["duplicate_event_id"] == 1
        assert report.valid_events[0].trial_index == 0

    def test_mixed_batch_reports_every_rejection_with_a_reason(self) -> None:
        batch = [
            valid_event(id="ok"),
            incomplete_event(),
            unknown_game_event(id="unknown"),
        ]
        report = validate_batch(batch)
        assert report.usable_count == 1
        assert report.dropped_count == 2
        assert all(record.issues for record in report.rejected_records)

    def test_warnings_on_valid_events_are_preserved_not_discarded(self) -> None:
        report = validate_batch([undocumented_error_class_event(id="w1")])
        assert report.usable_count == 1
        assert "w1" in report.valid_event_warnings
        assert report.valid_event_warnings["w1"][0].code == "undocumented_error_class_value"

    def test_empty_batch_produces_an_empty_report(self) -> None:
        report = validate_batch([])
        assert report.total_input_count == 0
        assert report.usable_count == 0
        assert report.dropped_count == 0
        assert report.data_quality_summary == {}
