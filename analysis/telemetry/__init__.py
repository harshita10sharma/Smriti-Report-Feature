"""Telemetry validation and adaptation.

Converts raw, untrusted telemetry payloads into validated
``analysis.models.telemetry`` objects. Nothing here interprets the
undocumented ``metrics`` jsonb payload's per-game keys - that
interpretation is the responsibility of the game-specific extractors
(a later phase) built against the registry's ``TelemetrySource``
gates (see REPORT_READINESS_AUDIT.md and ``analysis.registry``).
"""
