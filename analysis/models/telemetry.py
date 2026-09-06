"""Telemetry domain objects.

``TelemetryEvent`` and ``Session`` are typed mirrors of the reference
backend's real ``events`` and ``sessions`` tables (verified column-by-
column in REPORT_READINESS_AUDIT.md S3/S4) - they are deliberately
permissive (most fields optional, unknown extra fields preserved)
because that is what the actual schema allows: most columns are
nullable and the DB enforces almost no format beyond the `domain`
CHECK constraint.

``Trial`` is a distinct, stricter object: the normalized, analysis-
ready representation that game-specific extractors consume. Turning a
raw ``TelemetryEvent`` into a ``Trial`` is the adapter step described
in the master specification S75 ("separate backend/raw representation
from internal analytical representation"); that mapping logic
(including how to interpret the still-undocumented ``metrics`` jsonb
payload per game) is deferred to the telemetry-validation phase, not
implemented here. Phase 1 only establishes the two shapes.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from analysis.models.enums import Domain


class TelemetryEvent(BaseModel):
    """One raw row from the reference backend's ``events`` table.

    Immutable, matching the table's RLS policy (device insert-only;
    update/delete denied to every role - REPORT_READINESS_AUDIT.md
    S3). ``extra="allow"`` preserves any column this model does not
    yet know about, rather than silently dropping it - schema drift
    should surface as an extra field, not as lost data.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    id: str
    patient_id: str
    session_id: str
    game_id: str
    domain: Domain
    item_id: str | None = None
    item_difficulty: float | None = None
    theta_before: float | None = None
    correct: bool | None = None
    initiation_ms: int | None = None
    movement_ms: int | None = None
    response_time_ms: int | None = None
    chosen_id: str | None = None
    error_class: str | None = None
    trial_index: int | None = None
    trial_context: str | None = None
    hint_level: int = 0
    metrics: dict[str, object] = Field(default_factory=dict)
    ts: int
    hour_of_day: int | None = None
    tz_offset_min: int | None = None
    server_received_at: datetime | None = None


class Session(BaseModel):
    """One raw row from the reference backend's ``sessions`` table.

    ``game_ids`` is kept as the raw text column verbatim: its actual
    encoding (single ID vs. delimited list vs. JSON array) is
    unverified (REPORT_READINESS_AUDIT.md S4) and must not be guessed
    at here.
    """

    model_config = ConfigDict(frozen=True, extra="allow")

    id: str
    patient_id: str
    started_at: int
    ended_at: int | None = None
    game_ids: str
    completed: bool | None = None
    abandoned_at_ms: int | None = None
    demo_replays: int | None = None
    server_received_at: datetime | None = None


class Trial(BaseModel):
    """One normalized, analysis-ready trial.

    Produced by the telemetry-validation/adapter layer from a
    ``TelemetryEvent`` whose required trial fields are present and
    well-formed. Strict (``extra="forbid"``) because, unlike the raw
    event mirror, this is an internal contract this project fully
    controls.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    event_id: str
    patient_id: str
    session_id: str
    game_id: str
    domain: Domain
    trial_index: int | None
    item_id: str | None
    difficulty: float | None
    correct: bool | None
    response_time_ms: int | None
    error_class: str | None
    trial_context: str | None
    metrics: dict[str, object]
    ts: int
