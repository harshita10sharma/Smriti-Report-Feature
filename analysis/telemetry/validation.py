"""Telemetry validation (master spec S33).

Two entry points: ``validate_event`` for one raw payload, and
``validate_batch`` for a full ingestion batch (which additionally
checks for duplicate event ids across the batch). Neither ever
raises for a malformed *record* - malformed input is data, not a
programming error - they only ever return structured results.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

import pydantic

from analysis.models.enums import ValidationSeverity
from analysis.models.telemetry import TelemetryEvent
from analysis.telemetry.game_id_mapping import resolve_game_id
from analysis.telemetry.validation_models import (
    RejectedRecord,
    TelemetryValidationReport,
    ValidationIssue,
)

#: error_class values documented in the reference backend's events
#: table comment (REPORT_READINESS_AUDIT.md S3). Not DB-enforced, so a
#: value outside this set is a WARNING (still usable), not an ERROR.
_DOCUMENTED_ERROR_CLASS_VALUES = frozenset(
    {
        "semantic",
        "random",
        "perseverative",
        "repeat_selection",
        "omission",
        "mirror",
        "rotation",
        "detail",
        "sequence_error",
        "item_error",
        "miss",
        "false_alarm",
    }
)

#: trial_context values documented in the same column comment. Only
#: "post_switch" is documented (REPORT_READINESS_AUDIT.md S4) - the
#: others listed here are the specification's own vocabulary, kept
#: separate so an undocumented value is still just a WARNING.
_DOCUMENTED_TRIAL_CONTEXT_VALUES = frozenset(
    {"post_switch", "first_exposure", "repeat_exposure", "delayed_recall"}
)


def _extract_raw_id(raw: Mapping[str, object]) -> str | None:
    raw_id = raw.get("id")
    return raw_id if isinstance(raw_id, str) else None


def _non_negative_duration_issue(
    field: str, value: object
) -> ValidationIssue | None:
    if isinstance(value, int | float) and value < 0:
        return ValidationIssue(
            code="impossible_negative_duration",
            severity=ValidationSeverity.ERROR,
            message=f"{field} must not be negative, got {value}",
            field=field,
        )
    return None


def validate_event(
    raw: Mapping[str, object],
) -> tuple[TelemetryEvent | None, tuple[ValidationIssue, ...]]:
    """Validate one raw telemetry payload.

    Returns ``(event, issues)`` where ``event`` is ``None`` whenever
    at least one issue has ERROR severity - callers must treat a
    non-``None`` event as usable even if warnings are present.
    """
    try:
        event = TelemetryEvent.model_validate(raw)
    except pydantic.ValidationError as exc:
        structural_issues = tuple(
            ValidationIssue(
                code="structural_validation_error",
                severity=ValidationSeverity.ERROR,
                message=error["msg"],
                field=".".join(str(part) for part in error["loc"]) or None,
            )
            for error in exc.errors()
        )
        return None, structural_issues

    issues: list[ValidationIssue] = []

    if resolve_game_id(event.game_id) is None:
        issues.append(
            ValidationIssue(
                code="unknown_game_id",
                severity=ValidationSeverity.ERROR,
                message=f"game_id {event.game_id!r} does not resolve to a canonical GameId",
                field="game_id",
            )
        )

    if event.ts <= 0:
        issues.append(
            ValidationIssue(
                code="invalid_timestamp",
                severity=ValidationSeverity.ERROR,
                message=f"ts must be a positive epoch-ms value, got {event.ts}",
                field="ts",
            )
        )

    for field_name, value in (
        ("initiation_ms", event.initiation_ms),
        ("movement_ms", event.movement_ms),
        ("response_time_ms", event.response_time_ms),
    ):
        duration_issue = _non_negative_duration_issue(field_name, value)
        if duration_issue is not None:
            issues.append(duration_issue)

    if event.hint_level < 0:
        issues.append(
            ValidationIssue(
                code="impossible_negative_value",
                severity=ValidationSeverity.ERROR,
                message=f"hint_level must not be negative, got {event.hint_level}",
                field="hint_level",
            )
        )

    if event.trial_index is not None and event.trial_index < 0:
        issues.append(
            ValidationIssue(
                code="impossible_negative_value",
                severity=ValidationSeverity.ERROR,
                message=f"trial_index must not be negative, got {event.trial_index}",
                field="trial_index",
            )
        )

    if event.item_difficulty is not None and not math.isfinite(event.item_difficulty):
        issues.append(
            ValidationIssue(
                code="invalid_difficulty",
                severity=ValidationSeverity.ERROR,
                message=f"item_difficulty must be finite, got {event.item_difficulty}",
                field="item_difficulty",
            )
        )

    if event.error_class is not None and event.error_class not in _DOCUMENTED_ERROR_CLASS_VALUES:
        issues.append(
            ValidationIssue(
                code="undocumented_error_class_value",
                severity=ValidationSeverity.WARNING,
                message=f"error_class {event.error_class!r} is not a documented value",
                field="error_class",
            )
        )

    if (
        event.trial_context is not None
        and event.trial_context not in _DOCUMENTED_TRIAL_CONTEXT_VALUES
    ):
        issues.append(
            ValidationIssue(
                code="undocumented_trial_context_value",
                severity=ValidationSeverity.WARNING,
                message=f"trial_context {event.trial_context!r} is not a documented value",
                field="trial_context",
            )
        )

    has_error = any(issue.severity == ValidationSeverity.ERROR for issue in issues)
    return (None if has_error else event, tuple(issues))


def validate_batch(raw_events: list[Mapping[str, object]]) -> TelemetryValidationReport:
    """Validate a full batch, additionally rejecting duplicate event ids.

    The *first* occurrence of a given id is kept (if otherwise valid);
    every subsequent occurrence is rejected as a duplicate, even if it
    is itself structurally valid - master spec S33: detect duplicate
    events.
    """
    valid_events: list[TelemetryEvent] = []
    valid_event_warnings: dict[str, tuple[ValidationIssue, ...]] = {}
    rejected_records: list[RejectedRecord] = []
    data_quality_summary: dict[str, int] = {}
    seen_ids: set[str] = set()

    def _tally(issues: tuple[ValidationIssue, ...]) -> None:
        for issue in issues:
            data_quality_summary[issue.code] = data_quality_summary.get(issue.code, 0) + 1

    for raw in raw_events:
        event, issues = validate_event(raw)
        raw_id = _extract_raw_id(raw)

        if event is not None and raw_id is not None and raw_id in seen_ids:
            duplicate_issue = ValidationIssue(
                code="duplicate_event_id",
                severity=ValidationSeverity.ERROR,
                message=f"event id {raw_id!r} was already seen earlier in this batch",
                field="id",
            )
            issues = (*issues, duplicate_issue)
            event = None

        _tally(issues)

        if event is not None:
            if raw_id is not None:
                seen_ids.add(raw_id)
            valid_events.append(event)
            if issues:
                valid_event_warnings[event.id] = issues
        else:
            rejected_records.append(RejectedRecord(raw_id=raw_id, issues=issues))

    return TelemetryValidationReport(
        valid_events=tuple(valid_events),
        valid_event_warnings=valid_event_warnings,
        rejected_records=tuple(rejected_records),
        total_input_count=len(raw_events),
        data_quality_summary=data_quality_summary,
    )
