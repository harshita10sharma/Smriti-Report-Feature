"""Structured telemetry-validation results (master spec S33).

Validation never silently discards a record: every rejection carries
at least one ``ValidationIssue`` explaining why, and every accepted
record's non-fatal issues are preserved as warnings rather than
dropped.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, model_validator

from analysis.models.enums import ValidationSeverity
from analysis.models.telemetry import TelemetryEvent


class ValidationIssue(BaseModel):
    """One specific problem found with one telemetry record."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    code: str
    severity: ValidationSeverity
    message: str
    field: str | None = None


class RejectedRecord(BaseModel):
    """A telemetry record that could not be used, and why.

    ``raw_id`` is a best-effort identifier extracted from the raw
    payload (e.g. its ``id`` field if present and a string) - it is
    ``None`` when the payload was malformed enough that not even an
    id could be recovered.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    raw_id: str | None
    issues: tuple[ValidationIssue, ...]

    @model_validator(mode="after")
    def _has_at_least_one_error_issue(self) -> RejectedRecord:
        if not self.issues:
            raise ValueError("a RejectedRecord must carry at least one issue")
        if not any(issue.severity == ValidationSeverity.ERROR for issue in self.issues):
            raise ValueError(
                "a RejectedRecord must carry at least one ERROR-severity "
                "issue - a record with only warnings must not be rejected"
            )
        return self


class TelemetryValidationReport(BaseModel):
    """The full result of validating one batch of raw telemetry."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    valid_events: tuple[TelemetryEvent, ...]
    valid_event_warnings: dict[str, tuple[ValidationIssue, ...]]
    rejected_records: tuple[RejectedRecord, ...]
    total_input_count: int
    data_quality_summary: dict[str, int]

    @property
    def usable_count(self) -> int:
        return len(self.valid_events)

    @property
    def dropped_count(self) -> int:
        return len(self.rejected_records)

    @model_validator(mode="after")
    def _counts_are_consistent(self) -> TelemetryValidationReport:
        if self.usable_count + self.dropped_count != self.total_input_count:
            raise ValueError(
                f"usable_count ({self.usable_count}) + dropped_count "
                f"({self.dropped_count}) != total_input_count "
                f"({self.total_input_count})"
            )
        return self
