import pydantic
import pytest

from analysis.models.enums import ValidationSeverity
from analysis.telemetry.validation_models import (
    RejectedRecord,
    TelemetryValidationReport,
    ValidationIssue,
)


def _error_issue(code: str = "some_error") -> ValidationIssue:
    return ValidationIssue(code=code, severity=ValidationSeverity.ERROR, message="x")


def _warning_issue(code: str = "some_warning") -> ValidationIssue:
    return ValidationIssue(code=code, severity=ValidationSeverity.WARNING, message="x")


def test_rejected_record_requires_at_least_one_issue() -> None:
    with pytest.raises(pydantic.ValidationError, match="at least one issue"):
        RejectedRecord(raw_id="e1", issues=())


def test_rejected_record_requires_an_error_severity_issue() -> None:
    with pytest.raises(pydantic.ValidationError, match="at least one ERROR-severity"):
        RejectedRecord(raw_id="e1", issues=(_warning_issue(),))


def test_rejected_record_with_error_and_warning_is_valid() -> None:
    record = RejectedRecord(raw_id="e1", issues=(_warning_issue(), _error_issue()))
    assert len(record.issues) == 2


def test_report_rejects_inconsistent_counts() -> None:
    rejected = RejectedRecord(raw_id="e1", issues=(_error_issue(),))
    with pytest.raises(pydantic.ValidationError, match="!="):
        TelemetryValidationReport(
            valid_events=(),
            valid_event_warnings={},
            rejected_records=(rejected,),
            total_input_count=5,
            data_quality_summary={},
        )


def test_report_counts_are_derived_correctly() -> None:
    rejected = RejectedRecord(raw_id="e1", issues=(_error_issue(),))
    report = TelemetryValidationReport(
        valid_events=(),
        valid_event_warnings={},
        rejected_records=(rejected, rejected),
        total_input_count=2,
        data_quality_summary={"some_error": 2},
    )
    assert report.usable_count == 0
    assert report.dropped_count == 2
