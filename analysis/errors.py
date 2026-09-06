"""Explicit exception hierarchy for the Report Engine.

Every raised error in this codebase should be one of these types (or a
subclass defined alongside the module that needs it), never a bare
``Exception`` or ``ValueError``. This lets API/job entry points map
failures to stable error codes without inspecting message strings.
"""

from __future__ import annotations


class ReportEngineError(Exception):
    """Base class for all errors raised by the Report Engine."""


class ConfigurationError(ReportEngineError):
    """Required configuration is missing or invalid at startup."""


class TelemetryValidationError(ReportEngineError):
    """A telemetry record failed structural or semantic validation.

    Raised only for records that cannot be processed at all (e.g. an
    unknown patient_id type). Records that are merely low-quality
    should be represented via a validation result with warnings, not
    raised as an exception - see ``analysis.telemetry.validation``.
    """


class UnknownGameError(ReportEngineError):
    """A telemetry record references a game_id not in the registry."""


class RegistryError(ReportEngineError):
    """The game/metric/domain registry is internally inconsistent."""


class InsufficientEvidenceError(ReportEngineError):
    """An analytical step was asked to produce a conclusion it cannot
    responsibly support given the available evidence.

    Callers should generally prefer an explicit ``INSUFFICIENT_DATA``
    quality/status value over catching this exception - it exists for
    cases where returning a partial result would be misleading rather
    than merely incomplete.
    """


class ReportGenerationError(ReportEngineError):
    """Report assembly failed after analytics completed successfully."""


class PatientIsolationError(ReportEngineError):
    """An operation would have crossed a patient_id boundary.

    This is a defensive/last-resort error: patient scoping should be
    enforced structurally (every query and computation takes an
    explicit patient_id), and this exception exists to fail loudly if
    that invariant is ever violated rather than silently mixing data.
    """
