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


class AggregationMethod(StrEnum):
    """How multiple trial/session-level values are combined into one
    metric observation. Chosen per metric, never applied blindly -
    see master spec S5/S37 ("do not average incompatible metrics
    merely because they are numeric")."""

    MEAN = "mean"
    MEDIAN = "median"
    MAX_ACHIEVED = "max_achieved"
    RATE = "rate"
    DIFFERENCE = "difference"
    STDDEV = "stddev"
    COUNT = "count"


class TelemetrySource(StrEnum):
    """How confident this project is that a metric's required
    telemetry actually exists in the reference backend, per the
    Phase 0 audit (REPORT_READINESS_AUDIT.md S4).

    This is not a data-quality signal about any particular patient's
    data - it is a *registry-design-time* signal about whether this
    project has verified the underlying column/field exists at all.
    """

    #: Backed directly by a column verified to exist on events/sessions.
    VERIFIED_COLUMN = "verified_column"
    #: Computable purely from verified columns (e.g. a rate or a
    #: difference of two verified-column values).
    DERIVED_FROM_VERIFIED_COLUMNS = "derived_from_verified_columns"
    #: Expected to live inside the undocumented `metrics` jsonb
    #: payload. Per REPORT_READINESS_AUDIT.md S4/S13, this column's
    #: internal per-game shape is not documented anywhere accessible
    #: to this project - required key names here are proposed, not
    #: confirmed, and must be validated defensively at runtime.
    METRICS_JSONB_UNVERIFIED = "metrics_jsonb_unverified"
    #: Requires joining to a different table (e.g. `memos`) whose
    #: association to this event/session is not documented.
    CROSS_TABLE_UNVERIFIED = "cross_table_unverified"


class BaselineStatus(StrEnum):
    """Whether a personal baseline is usable for comparison yet.

    A baseline is never assumed valid merely because calendar days
    have elapsed (master spec S38) - it must meet explicit minimum
    evidence requirements before becoming ``ESTABLISHED``.
    """

    ESTABLISHING = "establishing"
    INSUFFICIENT_DATA = "insufficient_data"
    ESTABLISHED = "established"
