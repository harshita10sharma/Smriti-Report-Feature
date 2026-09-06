"""Application entry point.

This is intentionally minimal at the foundation stage: it verifies
the package is installed and importable, and reports version
metadata. The HTTP API (health check, analysis trigger, report
retrieval) is a later phase's responsibility, not this one.
"""

from __future__ import annotations

from analysis import (
    ANALYSIS_VERSION,
    API_VERSION,
    REGISTRY_VERSION,
    REPORT_SCHEMA_VERSION,
    TELEMETRY_SCHEMA_VERSION,
)
from analysis.config import load_settings
from analysis.logging import configure_logging, get_logger


def main() -> None:
    settings = load_settings()
    configure_logging(settings.log_level)
    logger = get_logger(__name__)
    logger.info(
        "smriti report engine starting",
        extra={
            "fields": {
                "api_version": API_VERSION,
                "report_schema_version": REPORT_SCHEMA_VERSION,
                "telemetry_schema_version": TELEMETRY_SCHEMA_VERSION,
                "analysis_version": ANALYSIS_VERSION,
                "registry_version": REGISTRY_VERSION,
            }
        },
    )
    print(f"smriti-report-engine analysis_version={ANALYSIS_VERSION}")


if __name__ == "__main__":
    main()
