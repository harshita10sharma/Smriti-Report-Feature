import pytest

from analysis.errors import (
    ConfigurationError,
    InsufficientEvidenceError,
    PatientIsolationError,
    RegistryError,
    ReportEngineError,
    ReportGenerationError,
    TelemetryValidationError,
    UnknownGameError,
)

ALL_ERROR_TYPES = [
    ConfigurationError,
    TelemetryValidationError,
    UnknownGameError,
    RegistryError,
    InsufficientEvidenceError,
    ReportGenerationError,
    PatientIsolationError,
]


@pytest.mark.parametrize("error_type", ALL_ERROR_TYPES)
def test_every_error_type_is_a_report_engine_error(
    error_type: type[Exception],
) -> None:
    assert issubclass(error_type, ReportEngineError)


def test_report_engine_error_is_catchable_as_exception() -> None:
    with pytest.raises(ReportEngineError):
        raise PatientIsolationError("cross-patient access attempted")
