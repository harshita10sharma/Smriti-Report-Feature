"""Controlled vocabularies used throughout the Report Engine.

Every state that must remain deterministic and machine-comparable
(domains, report status, data quality, etc.) is represented as an
enum here rather than as an arbitrary string, per the master
specification's type-safety requirement (S73).
"""

from __future__ import annotations

from enum import StrEnum


class Domain(StrEnum):
    """The five independent cognitive domains.

    There is deliberately no sixth "overall cognition" value - see
    the master specification's prohibition on a single black-box
    cognitive score. Values match the reference backend's
    ``events.domain`` CHECK constraint exactly (verified in
    REPORT_READINESS_AUDIT.md S3), so no translation layer is needed
    when reading real telemetry.
    """

    MEMORY = "memory"
    ATTENTION = "attention"
    EXECUTIVE = "executive"
    VISUOSPATIAL = "visuospatial"
    LANGUAGE = "language"


class GameId(StrEnum):
    """The nine canonical games in the current roster.

    These are IDs this project defines. The reference backend's
    ``events.game_id`` column is free text with no FK/enum
    constraint (REPORT_READINESS_AUDIT.md S3/S14), so the actual
    strings a game client sends are not guaranteed to match these
    exactly until confirmed - see the audit's open questions. All
    telemetry adapters must map an incoming raw game_id string onto
    one of these values explicitly, never assume they are identical.
    """

    FACES_OF_MY_FAMILY = "faces_of_my_family"
    MARKET_BASKET = "market_basket"
    SORT_THE_HARVEST = "sort_the_harvest"
    TRACE_THE_PATH = "trace_the_path"
    MY_DAY = "my_day"
    LAMPS_OF_THE_FESTIVAL = "lamps_of_the_festival"
    NAME_THE_HARVEST = "name_the_harvest"
    WEAVING_PATTERNS = "weaving_patterns"
    SOUNDS_OF_HOME = "sounds_of_home"


class Direction(StrEnum):
    """Whether a higher or lower metric value is favorable.

    Some metrics are context-specific and cannot be assigned a
    single global direction; those must be modeled explicitly by
    their MetricDefinition rather than forced into this enum.
    """

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class MetricType(StrEnum):
    """The three broad metric categories (master spec S21)."""

    PERFORMANCE = "performance"
    BEHAVIOURAL = "behavioural"
    STRUCTURAL_ERROR_PATTERN = "structural_error_pattern"


class QualityStatus(StrEnum):
    """Data-quality/evidence-sufficiency state for an analytical layer.

    Distinguishes "no evidence of change" from "not enough data to
    determine change" - these are not equivalent (master spec S60).
    """

    SUFFICIENT = "sufficient"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"
    UNAVAILABLE = "unavailable"


class ReportStatus(StrEnum):
    """Deterministic, top-level report state.

    This is a report *state*, not a cognitive score - it summarizes
    evidence sufficiency and trajectory shape, never a single number
    standing in for "how the person is doing."
    """

    ESTABLISHING_BASELINE = "establishing_baseline"
    INSUFFICIENT_DATA = "insufficient_data"
    STABLE = "stable"
    IMPROVING = "improving"
    FLUCTUATING = "fluctuating"
    CHANGE_WORTH_MENTIONING = "change_worth_mentioning"


class EvidenceSeverity(StrEnum):
    """How strongly an evidence object supports its conclusion."""

    INFO = "info"
    MODERATE = "moderate"
    HIGH = "high"


class ChangeType(StrEnum):
    """The shape of a detected longitudinal change."""

    STABLE = "stable"
    GRADUAL_CHANGE = "gradual_change"
    ABRUPT_CHANGE = "abrupt_change"
    FLUCTUATING = "fluctuating"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class BaselineStatus(StrEnum):
    """Whether a personal baseline is usable for comparison yet.

    A baseline is never assumed valid merely because calendar days
    have elapsed (master spec S38) - it must meet explicit minimum
    evidence requirements before becoming ``ESTABLISHED``.
    """

    ESTABLISHING = "establishing"
    INSUFFICIENT_DATA = "insufficient_data"
    ESTABLISHED = "established"
