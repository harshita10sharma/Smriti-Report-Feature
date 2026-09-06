import json

import pytest

from analysis.logging import configure_logging, get_logger


def test_configure_logging_does_not_stack_duplicate_handlers(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("DEBUG")
    configure_logging("DEBUG")
    logger = get_logger("test.logging.idempotent")
    logger.info("only once")
    captured = capsys.readouterr()
    matching_lines = [
        line for line in captured.out.strip().splitlines() if "only once" in line
    ]
    assert len(matching_lines) == 1


def test_log_output_is_valid_json_with_expected_fields(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("DEBUG")
    logger = get_logger("test.logging")
    logger.info(
        "telemetry validated",
        extra={"fields": {"patient_id": "p1", "valid_count": 3}},
    )
    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)
    assert payload["level"] == "INFO"
    assert payload["message"] == "telemetry validated"
    assert payload["patient_id"] == "p1"
    assert payload["valid_count"] == 3
    assert "timestamp" in payload


def test_forbidden_field_names_are_rejected() -> None:
    configure_logging("DEBUG")
    logger = get_logger("test.logging")
    with pytest.raises(ValueError, match="looks like a secret"):
        logger.info("bad", extra={"fields": {"api_key": "should-not-log"}})


def test_log_call_without_fields_does_not_raise(
    capsys: pytest.CaptureFixture[str],
) -> None:
    configure_logging("DEBUG")
    logger = get_logger("test.logging")
    logger.info("plain message")
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip().splitlines()[-1])
    assert payload["message"] == "plain message"
