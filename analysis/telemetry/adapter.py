"""Adapts a validated ``TelemetryEvent`` into the stricter ``Trial``
shape game-specific extractors will consume (master spec S75).

This is a purely structural mapping: it copies verified columns
across and passes the raw ``metrics`` payload through unchanged. It
never inspects or interprets ``metrics``' internal per-game keys -
that interpretation belongs to the game-specific extractors (a later
phase), which must consult the registry's ``TelemetrySource`` gates
before trusting any jsonb key (see ``analysis.registry``).

Only events that ``analysis.telemetry.validation.validate_event`` has
already accepted should be passed here - this function assumes its
input is already valid and does not re-validate.
"""

from __future__ import annotations

from analysis.models.telemetry import TelemetryEvent, Trial


def event_to_trial(event: TelemetryEvent) -> Trial:
    """Build a ``Trial`` from one already-validated ``TelemetryEvent``."""
    return Trial(
        event_id=event.id,
        patient_id=event.patient_id,
        session_id=event.session_id,
        game_id=event.game_id,
        domain=event.domain,
        trial_index=event.trial_index,
        item_id=event.item_id,
        difficulty=event.item_difficulty,
        correct=event.correct,
        response_time_ms=event.response_time_ms,
        error_class=event.error_class,
        trial_context=event.trial_context,
        metrics=dict(event.metrics),
        ts=event.ts,
    )
