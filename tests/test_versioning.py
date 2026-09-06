from analysis import versioning


def test_all_version_axes_are_non_empty_strings() -> None:
    for value in (
        versioning.API_VERSION,
        versioning.REPORT_SCHEMA_VERSION,
        versioning.TELEMETRY_SCHEMA_VERSION,
        versioning.ANALYSIS_VERSION,
        versioning.REGISTRY_VERSION,
    ):
        assert isinstance(value, str)
        assert value != ""


def test_version_axes_are_independent_objects() -> None:
    # Each axis must be its own value, not accidentally aliased to
    # another, so bumping one never silently bumps another.
    axes = {
        "api": versioning.API_VERSION,
        "report_schema": versioning.REPORT_SCHEMA_VERSION,
        "telemetry_schema": versioning.TELEMETRY_SCHEMA_VERSION,
        "analysis": versioning.ANALYSIS_VERSION,
        "registry": versioning.REGISTRY_VERSION,
    }
    assert len(axes) == 5
