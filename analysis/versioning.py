"""Centralized version metadata for the Report Engine.

Each axis is versioned independently so a breaking change in one
(e.g. the report JSON contract) does not silently imply a change in
another (e.g. the telemetry contract). Every report produced by this
engine must record these values so its output is reproducible: given
the same input telemetry and the same versions, the same result must
be produced.
"""

#: Version of the HTTP API surface (endpoints, request/response shapes).
API_VERSION = "0.1.0"

#: Version of the machine-readable report JSON contract.
REPORT_SCHEMA_VERSION = "0.1.0"

#: Version of the telemetry contract this engine validates events against.
TELEMETRY_SCHEMA_VERSION = "0.1.0"

#: Version of the analytical engine itself (metric/baseline/detection logic).
ANALYSIS_VERSION = "0.1.0"

#: Version of the game -> metric -> domain registry.
REGISTRY_VERSION = "0.1.0"
